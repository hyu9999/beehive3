import pickle
from datetime import datetime
from functools import partial

from stralib import UserConfig, Robot, SysConfig, FastTdate
from stralib.data_service.robot_data import RobotData
from typing import Dict, Any, List

from app.core.errors import PermissionDenied, NoDataError
from app.crud.base import get_robots_collection
from app.db.mongodb import db
from app.global_var import G
from app.models.fund_account import FundAccountPositionInDB, FundAccountInDB
from app.models.portfolio import Portfolio
from app.outer_sys.hq import get_security_price
from app.outer_sys.stralib.robot.utils import principle_to_robot, db2robot_position_mapping
from app.service.robots.tools import RobotTools
from app.utils.data_format import name_mapping
from app.utils.datetime import date2datetime


async def generate_sysconfig(dbrobot: Dict[str, Any], start_date: datetime, end_date: datetime) -> SysConfig:

    config = {
        "start_date": FastTdate.last_tdate(start_date),  # 机器人运行 往前取一天
        "end_date": end_date,
        "all_stock_sid_list": dbrobot["选股装备列表"],
        "all_timing_sid_list": dbrobot["择时装备列表"],
        "all_risk_sid_list": dbrobot["风控装备列表"],
        "all_tstock_tsid_list": dbrobot["交易装备列表"],
    }
    sys_config = SysConfig(**config)
    return sys_config


async def robot_source_data(dbrobot: Dict[str, Any], start_date: datetime, end_date: datetime) -> RobotData:
    """
    通过robot数据，构造stralib robot data
    Parameters
    ----------
    dbrobot 数据库查询robot结果
    start_date 开始日期
    end_date 开始日期
    Returns
    -------
    RobotData
    """
    sys_config = await generate_sysconfig(dbrobot, start_date, end_date)
    return RobotData(sys_config)


async def update_stralib_robot_data(sid: str, tdate: datetime):
    """
    更新某机器人robot data数据
    Parameters
    ----------
    sid
    tdate
    Returns
    -------

    """
    dbrobot = await get_robots_collection(db.client).find_one({"标识符": sid})
    robot_data = await robot_source_data(dbrobot, tdate, tdate)
    robot_data_bytes = pickle.dumps(robot_data)
    await G.preload_redis.set(f"stralib_robot_data_{sid}", robot_data_bytes, expire=3600 * 24)


async def get_stralib_robot_data(sid: str) -> RobotData:
    """获取某机器人robot data数据"""
    robot_data_bytes = await G.preload_redis.get(f"stralib_robot_data_{sid}", encoding=None)
    if not robot_data_bytes:
        raise NoDataError(message=f"未获取到robot_data缓存数据，请检查 {sid} 计算时间是否正常更新！")
    robot_data = pickle.loads(robot_data_bytes)
    return robot_data


async def account_robot_factory(portfolio: Portfolio) -> partial:
    """返回由组合信息配置的机器人"""
    robot = await RobotTools.get_portfolio_robot(portfolio.robot)
    if robot["标识符"].startswith("15"):
        raise PermissionDenied(message="15开头机器人不支持检测")
    tdate = robot["计算时间"]
    config = user_config_factory(
        robot,
        start_date=tdate,
        end_date=tdate,
        fundbal=0,
        mktval=0,
        stocks=[],
        fundid=str(portfolio.id),
        last_signals=[],
        run_type="service",
        **principle_to_robot(portfolio.robot_config),
    )
    robot_config = UserConfig.from_dict(config)
    source_data = await get_stralib_robot_data(portfolio.robot)
    return partial(Robot, tdate, rconfig=robot_config, all_data=source_data)


async def create_stralib_robot(
    portfolio: Portfolio,
    fund_account_assets: FundAccountInDB,
    fund_account_position: List[FundAccountPositionInDB]
) -> Robot:
    """构造stralib Robot."""
    b_robot = await RobotTools.get_portfolio_robot(portfolio.robot)
    if b_robot["标识符"].startswith("15"):
        raise PermissionDenied(message="15开头机器人不支持检测")
    tdate = b_robot["计算时间"]
    config = user_config_factory(
        b_robot,
        start_date=tdate,
        end_date=tdate,
        fundbal=float(fund_account_assets.cash.to_decimal()),
        mktval=float(fund_account_assets.securities.to_decimal()),
        stocks=await database_stock_list_to_robot(fund_account_position),
        fundid=str(portfolio.id),
        last_signals=[],
        **principle_to_robot(portfolio.robot_config),
    )

    asset = dict(fundbal=config.pop("fundbal"), mktval=config.pop("mktval"))
    stocks = config.pop("stocks")

    config = UserConfig.from_dict(config)
    source_data = await get_stralib_robot_data(portfolio.robot)
    robot = Robot(tdate, asset, stocks, config, source_data)
    return robot


def user_config_factory(
    b_robot: dict,
    *,
    start_date: datetime,
    end_date: datetime,
    fundbal: float,
    mktval: float,
    stocks: list,
    max_hold_day: int,
    max_hold_num: int,
    last_signals: list = None,
    tax_rate: float = 0.0016,
    fundid: str = None,
    run_type: str = "service",
) -> Dict[str, Any]:
    """
    根据投资原则和账户资金状况生成对应的配置, 用于组合装备运行
    Parameters
    ----------
    robot:           用户使用的机器人
    start_date:      开始时间
    end_date:        结束时间
    fundbal:        资金余额
    mktval:         市值
    stocks:          当前持仓
    max_hold_day:    投资原则, 最大持有天数
    max_hold_num:    投资原则, 最大持有数量
    last_signals:    开始时间前一天的信号
    tax_rate:        税率, 默认为 0.0016
    fundid:         资金账户 id
    run_type:
    """
    config = b_robot
    config.update(
        start_date=start_date,
        end_date=end_date,
        fundbal=fundbal,
        mktval=mktval,
        stocks=stocks,
        max_hold_day=max_hold_day,
        max_hold_num=max_hold_num,
        last_signals=last_signals,
        tax_rate=tax_rate,
        robot_name=b_robot["name"],
        fundid=fundid if fundid else "fundid",
        run_type=run_type,
    )
    return config


async def database_stock_list_to_robot(position_list: List[FundAccountPositionInDB]):
    return [await database_stock_to_robot(position) for position in position_list]


async def database_stock_to_robot(position: FundAccountPositionInDB, tdate: datetime = date2datetime()):
    """数据库中持仓格式转为机器人持仓格式."""
    exchange_mapping = {
        "CNSESH": "1",
        "CNSESZ": "0"
    }
    position_dict = position.dict()
    position_dict["tdate"] = tdate
    security = await get_security_price(symbol=position_dict["symbol"], exchange=exchange_mapping[position_dict["exchange"]])
    position_dict["mktval"] = position_dict["volume"] * float(security.current)
    position_dict["stopdown"] = 0
    position_dict["stopup"] = 999999
    stock_info = name_mapping(db2robot_position_mapping, position_dict, reverse=True)
    return stock_info
