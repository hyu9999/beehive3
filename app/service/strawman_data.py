from datetime import datetime

import pandas as pd
from hq2redis.models import SecurityHQ
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate
from stralib.adam.data_operator import get_strategy_signal
from stralib.adam.exceptions import AdamDataException

from app.core.errors import NoEquipError, StrategySignalError
from app.extentions import logger
from app.outer_sys.hq import get_security_hq
from app.crud.equipment import 查询某个装备的详情
from app.data_map.stock import SYMBOL_NAME_MAP


async def 获取选股信号列表(sid: str, start: datetime, end: datetime) -> pd.DataFrame:
    screen_df = get_strategy_signal(sid, start, end)
    if not screen_df.empty:
        screen_df = screen_df[screen_df.EXCHANGE.isin(["CNSESZ", "CNSESH"])][["TDATE", "EXCHANGE", "SYMBOL", "TCLOSE"]]
    if not screen_df.empty:
        screen_df.replace({"EXCHANGE": {"CNSESH": "1", "CNSESZ": "0"}}, inplace=True)
        hq_list = []
        for symbol, exchange in zip(*[getattr(screen_df, col).tolist()for col in ["SYMBOL", "EXCHANGE"]]):
            if symbol in [x["symbol"] for x in hq_list]:
                continue
            try:
                hq = await get_security_hq(symbol, exchange)
            except Exception as e:
                logger.warning(f"获取行情信息失败：{e}")
            else:
                hq_list.append(hq.dict())
        symbol_name_price = pd.DataFrame(hq_list)[["symbol", "symbol_name", "current"]]
        symbol_name_price.rename(columns={"current": "REALTIME_PRICE", "symbol_name": "SYMBOL_NAME", "symbol": "SYMBOL"}, inplace=True)
        result = pd.merge(screen_df, symbol_name_price, how="outer", on="SYMBOL", copy=False)
        result = result.where(pd.notna(result), None)
        return result
    return screen_df


async def 获取择时信号列表(sid: str, start: datetime, end: datetime, symbol_list: list) -> pd.DataFrame:
    timing_df = get_strategy_signal(sid, start, end)
    signals_list = list()
    for index_symbol in symbol_list:
        index_col = [f"market_trend_shape_{index_symbol}", f"position_rate_advice_{index_symbol}", f"position_rate_{index_symbol}"]
        columns = {f"market_trend_shape_{index_symbol}": "市场趋势形态", f"position_rate_{index_symbol}": "理想仓位", f"position_rate_advice_{index_symbol}": "建议仓位"}
        if f"valuation_quantile_{index_symbol}" in timing_df.columns:
            index_col.append(f"valuation_quantile_{index_symbol}")
            columns[f"valuation_quantile_{index_symbol}"] = "估值分位数"
        df = timing_df.reindex(columns=index_col)
        df.rename(columns=columns, inplace=True)
        df["指数"] = SYMBOL_NAME_MAP.get(index_symbol, None)
        df["信号日期"] = df.index
        signals_list.append(df)
    result = pd.concat(signals_list)
    return result


async def 获取某指数择时信号(sid: str, start: datetime, end: datetime, index_symbol: str) -> pd.DataFrame:
    timing_df = get_strategy_signal(sid, start, end)
    if timing_df.empty:
        start = end = FastTdate.last_tdate()
        timing_df = get_strategy_signal(sid, start, end)
    index_col = [f"market_trend_shape_{index_symbol}", f"position_rate_advice_{index_symbol}", f"position_rate_{index_symbol}"]
    columns = {f"market_trend_shape_{index_symbol}": "市场趋势形态", f"position_rate_{index_symbol}": "理想仓位", f"position_rate_advice_{index_symbol}": "建议仓位"}
    if f"valuation_quantile_{index_symbol}" in timing_df.columns:
        index_col.append(f"valuation_quantile_{index_symbol}")
        columns[f"valuation_quantile_{index_symbol}"] = "估值分位数"
    result = timing_df.reindex(columns=index_col)
    result.rename(columns=columns, inplace=True)
    result["指数"] = SYMBOL_NAME_MAP.get(index_symbol, None)
    result["信号日期"] = result.index
    return result


async def 获取风控信号列表(sid: str, start: datetime, end: datetime) -> pd.DataFrame:
    try:
        risk_df = get_strategy_signal(sid, start, end)
    except AdamDataException:
        raise StrategySignalError()
    if not risk_df.empty:
        risk_df = risk_df[risk_df.exchange.isin(["CNSESZ", "CNSESH"])][["tdate", "exchange", "symbol"]]
    if not risk_df.empty:
        risk_df.replace({"exchange": {"CNSESH": "1", "CNSESZ": "0"}}, inplace=True)
        hq_list = []
        for symbol, exchange in zip(*[getattr(risk_df, col).tolist() for col in ["symbol", "exchange"]]):
            if symbol in [x["symbol"] for x in hq_list]:
                continue
            try:
                hq = await get_security_hq(symbol, exchange)
            except Exception as e:
                logger.warning(f"获取行情信息失败：{e}")
            else:
                hq_list.append(hq.dict())
        symbol_name_price = pd.DataFrame(hq_list)[["symbol", "symbol_name", "current"]]
        symbol_name_price.rename(columns={"current": "realtime_price"}, inplace=True)
        result = pd.merge(risk_df, symbol_name_price, how="outer", on="symbol", copy=False)
        result = result.where(pd.notna(result), None)
        return result
    return risk_df


async def 获取风控信号数量(sid: str, start: datetime, end: datetime) -> int:
    risk_df = get_strategy_signal(sid, start, end)
    return risk_df[risk_df.exchange.isin({"CNSESH", "CNSESZ"})].shape[0]


async def 获取风控包最新信号(sid: str, conn: AsyncIOMotorClient):
    package = await 查询某个装备的详情(conn, sid)
    start = end = package.计算时间
    response_result = [
        {"标识符": eq_sid, "开始时间": start, "结束时间": end, "装备名称": (await 查询某个装备的详情(conn, eq_sid)).名称, "信号数量": await 获取风控信号数量(eq_sid, start, end)}
        for eq_sid in package.装备列表
    ]
    return response_result, start
