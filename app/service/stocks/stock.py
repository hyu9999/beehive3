from datetime import time
from typing import List, Dict, Union

import httpx
import pandas as pd
from hq2redis import HQSourceError
from stralib import RealtimeQuote, get_version_data

from app import settings
from app.enums.security import 证券交易所
from app.extentions import logger
from app.global_var import G


def get_stock_list_from_stralib() -> List[Dict[str, str]]:
    """获取股票列表."""
    df = get_version_data("md_sec_type").reset_index()[["S_INFO_WINDCODE", "SYMBOL", "EXCHANGE", "S_INFO_NAME", "INDUSTRIESNAME"]]
    df2 = get_version_data("md_security").reset_index()[["S_INFO_WINDCODE", "S_INFO_COMPNAME", "S_INFO_PINYIN"]]
    result = pd.merge(df2, df, on="S_INFO_WINDCODE", how="right")
    result = result[["SYMBOL", "EXCHANGE", "S_INFO_PINYIN", "S_INFO_NAME", "INDUSTRIESNAME"]]
    result = result.dropna()
    result.columns = [
        "symbol",
        "exchange",
        "symbol_shortname",
        "symbol_name",
        "industry",
    ]
    result.replace({"exchange": {"CNSESH": "1", "CNSESZ": "0"}}, inplace=True)
    return result.to_dict("records")


async def query_realtime_from_data_source(symbol: str, marketid: int) -> dict:
    """从建投的行情源查询股票行情"""
    if marketid in [0, "0"]:
        marketCd = 2
    elif marketid in ["1", 1]:
        marketCd = 1
    else:
        marketCd = None
    url = settings.hq.jiantou_url.format(symbol, marketCd)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code == 200:
        if response.json().get("status") == "OK":
            data = response.json().get("result")
            result = {
                "symbol": data["symbol"],
                "symbol_name": data["symbolName"],
                "exchange": marketid,
                "previous_close_price": float(data["prevClose"]),
                "opening_price": float(data["open"]),
                "today_low": float(data["low"]),
                "today_high": float(data["high"]),
                "realtime_price": float(data["consecutivePresentPrice"]),
            }
            return result
    logger.info(f"[查询股票实时行情链接错误，url:({url})，原因：{response.text}]")
    raise HQSourceError(response.text)


async def query_stock_price_from_jiantou(symbol_exchange_list: List[str], skip=0, limit=0) -> List[Dict]:
    """查询指定的股票的行情"""
    result = []
    for symbol_exchange in symbol_exchange_list:
        symbol, marketid = symbol_exchange.split("_")
        try:
            data = await query_realtime_from_data_source(symbol, marketid)
        except HQSourceError as e:
            logger.info(f"[查询股票({symbol}_{marketid})实时行情错误] {e}")
            continue
        result.append(data)
    return result


def query_stock_price(symbol_exchange_list: List[str], skip=0, limit=0) -> List[Dict]:
    """查询指定的股票的行情"""
    conditions = " or ".join(['`HQZQDM` = "{}" AND `marketid` = {}'.format(*x.split("_")) for x in symbol_exchange_list])
    sql = """SELECT
    `HQZQDM` as `symbol`,
    `HQZQJC` as `symbol_name`,
    cast(`marketid` as char) as `exchange`,
    `HQZRSP` as `previous_close_price`,
    `HQJRKP` as `opening_price`,
    `HQZDCJ` as `today_low`,
    `HQZGCJ` as `today_high`,
    (case when `HQJRKP` is null then `HQZRSP` else `HQZJCJ` end) as `realtime_price`
             FROM `realtime`
             WHERE {}
          """.format(
        conditions
    )
    if limit > 0:
        sql += f" limit {skip},{limit}"
    queryset = G.hq_mysql.query(sql)
    return queryset


def get_five_real_time_price(symbol: str, exchange: 证券交易所) -> Dict[str, Union[str, float, int, time, 证券交易所]]:
    """获取五档图数据"""
    if exchange == "0":
        stralib_exchange = "CNSESZ"
    else:
        stralib_exchange = exchange
    # 集合竞价期间无数据
    df = RealtimeQuote().get_realtime_quote(symbol=symbol, exchange=stralib_exchange)
    df["datetime"] = pd.to_datetime(df["datetime"], format="%H%M%S").apply(lambda x: x.time())
    data = df.to_dict()
    res = {"symbol": symbol, "exchange": exchange}
    for price_name in data:
        res[price_name[-4:].lower()] = [value for key, value in data[price_name].items()][0]
    return res
