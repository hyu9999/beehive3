from datetime import datetime
from smtplib import SMTPResponseException

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import get_strategy_signal

from app.crud.base import get_equipment_collection, get_collection_by_config
from app.crud.stock import get_favorite_stock_by_unique
from app.enums.equipment import 装备分类转换
from app.enums.user import 发送消息类型
from app.outer_sys.message.adaptor.mail import SendEmail
from app.outer_sys.message.send_msg import SendMessage
from app.schedulers import logger
from app.service.stocks.stock import query_stock_price
from app.service.strawman_data import 获取选股信号列表, 获取择时信号列表


async def get_package_signal(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, user: dict) -> tuple:
    """获取风控包信号"""
    equipment_info = await get_equipment_collection(conn).find_one({"标识符": sid})
    equipment_list = equipment_info["装备列表"] if equipment_info else []
    favorite_stock = await get_favorite_stock_by_unique(conn, {"category": "portfolio", "username": user["username"]})
    symbol_list = [stock.symbol for stock in favorite_stock.stocks] if favorite_stock else []
    result = pd.DataFrame()
    for sid in equipment_list:
        try:
            df = get_strategy_signal(sid, start, end)
            df = df[df["symbol"].isin(symbol_list)]
            df["risk"] = (await get_equipment_collection(conn).find_one({"标识符": sid})).get("策略话术")
            result = result.append(df, sort=False)
        except KeyError:
            continue
    if result.empty:
        return result
    try:
        result.reset_index(drop=True, inplace=True)
        result.drop(result[result.grade == "."].index, inplace=True)
        result["risk"] = result.apply(
            lambda x: "<br />".join(result[result.tdate.isin([x["tdate"]]) & result.symbol.isin([x["symbol"]])].risk.tolist()), axis=1
        )
        result = result[["tdate", "symbol", "exchange", "risk"]]
        result.drop_duplicates(keep="first", inplace=True)
        result.replace({"exchange": {"CNSESH": "1", "CNSESZ": "0"}}, inplace=True)
        args = ["{}_{}".format(s, e) for s, e in zip(*[getattr(result, col).tolist() for col in ["symbol", "exchange"]])]
        symbol_name = pd.DataFrame(query_stock_price(args))[["symbol", "symbol_name"]]
        result = pd.merge(result, symbol_name, how="outer", on="symbol", copy=False)
        result = result.where(pd.notna(result), None)
        result = result[["tdate", "symbol_name", "symbol", "risk"]]
        result.rename(columns={"tdate": "日期", "symbol_name": "股票名称", "symbol": "股票代码", "risk": "当前风险"}, inplace=True)
        return result
    except (AttributeError, KeyError, ValueError) as e:
        return result


async def get_appointed_real_signal(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime) -> pd.DataFrame:
    """大类资产配置、基金定投装备信号"""
    try:
        table_name = "大类资产配置实盘信号collection名" if sid.startswith("06") else "基金定投实盘信号collection名"
        cursor = get_collection_by_config(conn, table_name).find({"标识符": sid, "交易日期": {"$gte": start, "$lte": end}})
        df = pd.DataFrame([signal async for signal in cursor])
        df = df[~df.买卖方向.isin(["保持不变"])]
        df["个股仓位占比"] = df["个股仓位占比"].apply(lambda x: format(x, ".2%"))
        df["价格（元）"] = df.apply(lambda x: x["个股买入均价"] if x["买卖方向"] == "买入" else x["个股卖出均价"], axis=1)
        df = df[["交易日期", "证券名称", "证券代码", "买卖方向", "个股持仓变动", "价格（元）", "个股仓位占比"]]
        df.rename(columns={"交易日期": "时间", "证券名称": "股票名称", "证券代码": "股票代码", "买卖方向": "操作", "个股持仓变动": "股数", "个股仓位占比": "仓位"}, inplace=True)
        return df
    except (AttributeError, KeyError, ValueError) as e:
        return pd.DataFrame()


async def get_equipment_signal(conn: AsyncIOMotorClient, equipment: dict, start: datetime, end: datetime):
    """获取装备信号"""
    df = pd.DataFrame()
    if equipment["标识符"].startswith("02"):
        signals = await 获取选股信号列表(equipment["标识符"], start, end)
        if not signals.empty:
            df = signals[["TDATE", "SYMBOL_NAME", "SYMBOL", "REALTIME_PRICE"]]
            df.rename(columns={"TDATE": "日期", "SYMBOL_NAME": "股票名称", "SYMBOL": "股票代码", "REALTIME_PRICE": "入选价格"}, inplace=True)
    elif equipment["标识符"].startswith("03"):
        signals = await 获取择时信号列表(equipment["标识符"], start, end, equipment["指数列表"])
        if not signals.empty:
            df = signals[["信号日期", "指数", "市场趋势形态", "建议仓位"]]
    elif equipment["标识符"][:2] in ["06", "07"]:
        df = await get_appointed_real_signal(conn, equipment["标识符"], start, end)
    elif equipment["标识符"].startswith("11"):
        equipment_list = equipment["装备列表"] if equipment else []
        df = [get_strategy_signal(x, start, end) for x in equipment_list]
    return df


async def get_all_equipment_signals(conn: AsyncIOMotorClient, tdate: datetime, filters: dict = None):
    """获取所有装备的信号"""
    filters = filters or {"装备库版本": {"$ne": "3.3"}, "状态": {"$in": ["已上线"]}}
    equipments = get_equipment_collection(conn).find(filters)
    ret_data = {}
    async for equipment in equipments:
        signal = await get_equipment_signal(conn, equipment, tdate, tdate)
        if equipment["标识符"].startswith("11"):
            if signal:
                ret_data[equipment["标识符"]] = {"signal": signal, "equipment": equipment}
        else:
            if not signal.empty:
                ret_data[equipment["标识符"]] = {"signal": signal, "equipment": equipment}
    return ret_data


async def get_equipment_signal_by_user(conn: AsyncIOMotorClient, user: dict, tdate: datetime, signals: dict):
    """根据用户获取装备信号（包括用户创建和订阅的装备）"""
    content = ""
    try:
        equipment_list = user["equipment"]["subscribe_info"]["focus_list"] + user["equipment"]["create_info"]["running_list"]
    except KeyError:
        return content
    for sid in equipment_list:
        if sid.startswith("11"):
            df = await get_package_signal(conn, sid, tdate, tdate, user)
        else:
            df = signals[sid]["signal"] if sid in signals.keys() else pd.DataFrame()
        df.dropna(axis=0, how="any", inplace=True)
        if not df.empty:
            pd.set_option("display.max_colwidth", -1)
            html = df.to_html(index=False, justify="center", escape=False).replace("<table", '<table style="text-align: center;border-collapse:collapse"')
            content += f"<h3>{装备分类转换._value2member_map_[sid[:2]].name}装备：</h3><p>您订阅的{signals[sid]['equipment']['分类']}装备《{signals[sid]['equipment']['名称']}》，今日发出信号：</p>{html}"
    return content


async def send_message(user, content, tdate):
    """发送消息"""
    if not content:
        return False
    sm, params = None, None
    if user["send_type"] == 发送消息类型.email:
        sm = SendMessage(SendEmail())
        params = {"to_addr": user["email"], "title": f"智道-订阅装备信号 {tdate:%Y-%m-%d}", "content": content, "send_type": "html"}
    try:
        sm.send(**params)
    except SMTPResponseException as e:
        logger.error(f"Code:{e.smtp_code} Msg:{e.smtp_error.decode()}")
    except Exception as e:
        logger.error(f"{user['username']}消息发送失败！失败详情；{e}")
    else:
        return True
