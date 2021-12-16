from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import (
    get_equipment_collection,
    get_portfolio_collection,
    get_robots_collection,
    get_user_message_collection,
)
from app.enums.portfolio import 组合状态, 风险点状态, 风险类型
from app.enums.user import 消息分类, 消息类型
from app.extentions import logger
from app.models.base.portfolio import 风险点信息
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.outer_sys.hq import get_security_info, get_security_price
from app.outer_sys.stralib.robot.run_robot import create_stralib_robot
from app.service.fund_account.fund_account import (
    get_fund_account_position,
    get_fund_asset,
)
from app.service.risks.utils import risk_type_from_signal
from app.utils.market_convert import MarketConverter


async def risk_detection_by_robot(conn: AsyncIOMotorClient, robot_sid_list: List = None, send_msg=False):
    """
    根据使用的机器人筛选出来的组合执行风险检测

    Parameters
    ----------
    conn
    robot_sid_list
    send_msg

    Returns
    -------

    """
    filters = {
        "status": 组合状态.running,
        "robot": {"$in": robot_sid_list if robot_sid_list else [x["标识符"] async for x in get_robots_collection(conn).find({"状态": "已上线"})]},
    }
    portfolio_list = get_portfolio_collection(conn).find(filters)
    async for portfolio in portfolio_list:
        try:
            portfolio = await risk_detection(conn, Portfolio(**portfolio), send_msg=send_msg)
        except Exception as e:
            logger.error(f"【风险检测失败】[{e}]{portfolio['_id']}")


async def risk_detection(conn: AsyncIOMotorClient, portfolio: Portfolio, send_msg=True) -> Portfolio:
    """
    风险检测

    根据组合装备给出的信号, 生成并保存风险数据

    Parameters
    ----------
    conn
    portfolio
    send_msg

    Returns
    -------
    portfolio
    """
    # 非运行状态组合不进行风险检测
    if portfolio.status != 组合状态.running:
        return portfolio
    # 在解决中的状态时不进行新的检测
    if [x for x in portfolio.risks if x.status == 风险点状态.solving]:
        return portfolio
    fund_account = portfolio.fund_account[0]
    fund_account_assets = await get_fund_asset(conn, fund_account.fundid, portfolio.category, fund_account.currency)
    fund_account_position = await get_fund_account_position(conn, fund_account.fundid, portfolio.category)
    # 检测风险
    new_risks = await get_detect_all_risks(conn, portfolio, fund_account_assets, fund_account_position)
    # 保存风险
    await save_risks(conn, portfolio, new_risks)
    # 发送消息
    if send_msg:
        if new_risks:
            # 写入用户消息表：优化点待确认
            kwargs = {
                "title": f"{portfolio.name}",
                "content": f"当前有{len(new_risks)}个优化点等待确认",
                "category": 消息分类.portfolio,
                "msg_type": 消息类型.risk,
                "username": portfolio.username,
                "data_info": f"{portfolio.id}",
            }
            await get_user_message_collection(conn).insert_one(kwargs)
            # TODO 发送微信消息：有优化点等待确认
    return portfolio


async def get_detect_all_risks(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    fund_account_assets: FundAccountInDB,
    fund_account_position: List[FundAccountPositionInDB],
) -> List[风险点信息]:
    """获取当前组合所有风险点."""
    try:
        robot = await create_stralib_robot(portfolio, fund_account_assets, fund_account_position)
    except Exception as e:
        logger.error(f"[构建robot失败][{portfolio.id}]{e}")
        return []
    # 检测个股风险
    new_risks = await get_stock_risk(conn, robot, portfolio)
    # 检测仓位风险
    position_risk = await get_position_risk(robot)
    if position_risk:
        new_risks.append(position_risk)
    # 风险筛选
    all_risks = await filter_risks(new_risks, portfolio.risks, fund_account_position)
    return all_risks


async def save_risks(conn: AsyncIOMotorClient, portfolio: Portfolio, all_risks: List[风险点信息]):
    """
    存储风险点

    Parameters
    ----------
    conn
    portfolio
    risks

    Returns
    -------

    """
    portfolio.risks = all_risks
    portfolio.updated_at = datetime.utcnow()
    await get_portfolio_collection(conn).update_one({"_id": portfolio.id}, {"$set": portfolio.dict(include={"risks", "updated_at"})})


async def filter_risks(
    new_risks: List[风险点信息],
    old_risks: List[风险点信息],
    fund_account_position: List[FundAccountPositionInDB],
) -> List[风险点信息]:
    """
    筛选风险

    Parameters
    ----------
    new_risks
    old_risks
    account

    Returns
    -------

    """
    # 有数据：说明旧的风险重置过；无数据：需要将数据数据补充到风险列表中
    handled_list = [x for x in old_risks if x.status in [风险点状态.resolved, 风险点状态.unresolved]]
    old_risks = [] if handled_list else old_risks
    # 股票数量和可用数量为0的过滤掉
    symbol_list = {x.symbol: x.volume for x in fund_account_position}
    available_symbol_list = {x.symbol: x.available_volume for x in fund_account_position}
    new_risks = [x for x in new_risks if not x.symbol or all([symbol_list[x.symbol], available_symbol_list[x.symbol]])]
    old_risks_map = {f"{x.symbol}_{x.exchange}_{x.risk_type}": x for x in old_risks}
    risks = []
    for item in new_risks:
        old_risk = old_risks_map.get(f"{item.symbol}_{item.exchange}_{item.risk_type}")
        if old_risk:
            risks.append(old_risk)
        else:
            item.date = datetime.now()
            risks.append(item)
    return risks


async def signal_to_risk(conn: AsyncIOMotorClient, signal: dict, portfolio: Portfolio) -> Optional[风险点信息]:
    """
    个股风险时对应字段需要补全

    Parameters
    ----------
    conn
    signal 从组合装备机器人中获取到的 last_signals 中的字典
    portfolio

    Returns
    -------
    返回生成好的 Risk 实例
    """
    arg_dict = {}
    risk_type = risk_type_from_signal(signal)
    if not risk_type:
        return None

    arg_dict["risk_type"] = risk_type
    arg_dict["date"] = signal.get("TDATE")

    if risk_type in ["8", "9"]:
        arg_dict["name"] = "仓位过重" if risk_type == "8" else "仓位过轻"
    else:
        symbol = signal["SYMBOL"]
        exchange = MarketConverter.stralib(signal["MARKET"])
        security = await get_security_info(symbol, str(exchange))
        symbol_name = security.symbol_name
        arg_dict["symbol_name"] = symbol_name
        if risk_type == "10":
            arg_dict["name"] = "达到调仓周期"
            arg_dict["opinion"] = "您的持仓到达了组合的调仓周期，建议卖出"
        elif risk_type in ["2", "3", "4", "5", "6", "7"]:
            sid = f"04181114{signal.get('OPERATOR')}"
            equip_info = await get_equipment_collection(conn).find_one({"标识符": sid})
            if signal.get("OPERATOR") == "sjyj01":
                reason = "有审计意见类型风险"
            else:
                reason = equip_info["策略话术"]
            arg_dict["name"] = f'"{symbol_name}"{reason}'
            arg_dict["opinion"] = equip_info["策略话术"]
            arg_dict["data"] = await get_stock_risk_data(conn, signal)
        elif risk_type == "12":
            # TODO 多个交易装备同一只股票都产生信号时，会产生bug
            robot = await get_robots_collection(conn).find_one({"标识符": portfolio.robot})
            trade_sid = robot["交易装备列表"][0]
            equip_info = await get_equipment_collection(conn).find_one({"标识符": trade_sid})

            reason = "看多" if signal.get("SIGNAL") == 1 else "看空"
            content = f'"{symbol_name}"{equip_info["名称"]}指标出现{reason}信号'
            arg_dict["name"] = content
            opinion = equip_info["策略话术"]
            if type(opinion) == dict:
                opinion = opinion.get("('卖1',)", None)
            arg_dict["opinion"] = opinion
            arg_dict["data"] = await get_stock_risk_data(conn, signal)
        else:
            arg_dict["name"] = risk_type
        arg_dict["price"] = signal.get("TPRICE")
        arg_dict["symbol"] = symbol
        arg_dict["exchange"] = MarketConverter.stralib(signal["MARKET"])

    return 风险点信息(id=PyObjectId(), status=风险点状态.confirm, **arg_dict)


async def get_stock_risk(conn, robot, portfolio: Portfolio) -> List[风险点信息]:
    """
    获取个股风险

    Parameters
    ----------
    conn
    robot
    portfolio

    Returns
    -------
    risks
    """
    robot.get_hold_risk()
    risks = list(
        filter(
            None,
            [await signal_to_risk(conn, s, portfolio) for s in robot.all_risk_list],
        )
    )
    return risks


async def get_position_risk(robot) -> Optional[风险点信息]:
    """
    获取仓位风险

    Parameters
    ----------
    robot

    Returns
    -------
    risks
    """
    robot.check_position()
    adviced = [
        float(robot.timing_signal.split("-")[0]) / 100,
        float(robot.timing_signal.split("-")[1][:-1]) / 100,
    ]
    if adviced[0] > robot.current_position:
        name = "仓位过轻"
        risk_type = 风险类型.underweight
    elif adviced[1] < robot.current_position:
        name = "仓位过重"
        risk_type = 风险类型.overweight
    else:
        return None

    return 风险点信息(
        id=PyObjectId(),
        name=name,
        status=风险点状态.confirm,
        risk_type=risk_type,
        position_rate=robot.current_position,
        position_advice=adviced,
        date=datetime.today(),
    )


# TODO 通联数据源已经废弃，需要改为zvt数据源
async def get_stock_risk_data(conn: AsyncIOMotorClient, signal):
    """
    获取个股风险数据

    Parameters
    ----------
    conn
    signal

    Returns
    -------

    """

    operator = signal.get("OPERATOR")
    trade_date = signal.get("TDATE")
    symbol = signal.get("SYMBOL")
    exchange = MarketConverter.stralib(signal["MARKET"])
    if operator == "sjyj01":
        sid = f"04181114{operator}"
        equip_info = await get_equipment_collection(conn).find_one({"标识符": sid})
        reason = equip_info["策略话术"]
        data = [{"name": "审核意见", "value": reason}]
    elif operator == "yxfz01":
        result = "净有息负债率"
        data = [{"name": "净有息负债率", "value": result}]
    elif operator == "st0001":
        result = "被ST时间"
        data = [{"name": "被ST时间", "value": result}]
    elif operator == "pst001":
        data = [
            {"name": "股东权益", "value": "归属于母公司所有者权益合计"},
            {"name": "注册资本", "value": "注册资金"},
            {"name": "净利润", "value": "归属于母公司所有者的净利润"},
        ]
    elif operator == "8":
        security = await get_security_price(symbol, str(exchange))
        data = [
            {"name": "建议卖出价", "value": security.current},
            {"name": "时间", "value": trade_date},
        ]
    else:
        data = []
    return data
