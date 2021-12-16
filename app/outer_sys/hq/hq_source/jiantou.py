from datetime import datetime

import httpx
from hq2redis import HQSourceError
from hq2redis.models import SecurityInfo, SecurityPrice, SecurityHQ, SecurityTicks
from hq2redis.utils import get_security_meta

from app import settings
from app.outer_sys.hq.abc import HQSource


class JiantouHQ(HQSource):
    BASE_URL = settings.hq.jiantou_url
    JIANTOU_EXCHANGE_MAPPING = {"0": "2", "1": "1"}

    @classmethod
    async def _fetch(cls, symbol: str, exchange: str) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(cls.BASE_URL.format(symbol, cls.JIANTOU_EXCHANGE_MAPPING[exchange]))
            except httpx.ConnectTimeout as e:
                raise HQSourceError("请求建投API超时.") from e
            else:
                if response.status_code == 200:
                    json = response.json()
                    if json.get("status") == "OK":
                        return json["result"]
                raise HQSourceError(f"请求证券`{symbol}.{exchange}`失败, 接口返回值错误.")

    @classmethod
    def get_code(cls, symbol: str, exchange: str) -> str:
        ...

    @classmethod
    async def get_security_info(cls, symbol: str, exchange: str) -> SecurityInfo:
        """获取证券基本信息数据."""
        raise HQSourceError("该行情源未提供证券基本信息数据.")

    @classmethod
    async def get_security_price(cls, symbol: str, exchange: str) -> SecurityPrice:
        """获取证券价格数据."""
        json = await cls._fetch(symbol, exchange)
        data = get_security_meta(symbol)
        try:
            data.update({
                "symbol": symbol,
                "exchange": exchange,
                "code": f"{symbol}.{cls._get_hq2redis_code(symbol, exchange)}",
                "current": json["consecutivePresentPrice"]
            })
        except KeyError as e:
            raise HQSourceError(f"行情数据解析失败({e}).")
        return SecurityPrice(**data)

    @classmethod
    async def get_security_hq(cls, symbol: str, exchange: str) -> SecurityHQ:
        """获取证券行情数据."""
        json = await cls._fetch(symbol, exchange)
        data = get_security_meta(symbol)
        try:
            data.update({
                "symbol": symbol,
                "exchange": exchange,
                "code": f"{symbol}.{cls._get_hq2redis_code(symbol, exchange)}",
                "current": json["consecutivePresentPrice"],
                "date": datetime.strptime(json["baseDate"], "%Y%M%d"),
                "open": json["open"],
                "close": json["consecutivePresentPrice"],
                "high": json["high"],
                "low": json["low"],
                "pre_close": json["prevClose"],
                "symbol_name": json["symbolName"],
                "symbol_short_name": "",
                "category": "stock",
                "industry": ""
            })
        except KeyError as e:
            raise HQSourceError(f"行情数据解析失败({e}).")
        return SecurityHQ(**data)

    @classmethod
    async def get_security_ticks(cls, symbol: str, exchange: str) -> SecurityTicks:
        """获取证券Ticks数据."""
        json = await cls._fetch(symbol, exchange)
        data = get_security_meta(symbol)
        try:
            data.update({
                "symbol": symbol,
                "exchange": exchange,
                "code": f"{symbol}.{cls._get_hq2redis_code(symbol, exchange)}",
                "current": json["consecutivePresentPrice"],
                "high": json["high"],
                "low": json["low"],
                "ts": datetime.now().timestamp(),
                "bid1_p": json["bestBid1"],
                "bid2_p": json["bestBid2"],
                "bid3_p": json["bestBid3"],
                "bid4_p": json["bestBid4"],
                "bid5_p": json["bestBid5"],
                "ask1_p": json["GAP1"],
                "ask2_p": json["GAP2"],
                "ask3_p": json["GAP3"],
                "ask4_p": json["GAP4"],
                "ask5_p": json["GAP5"],
                "bid1_v": json["bestBidAmt1"],
                "bid2_v": json["bestBidAmt2"],
                "bid3_v": json["bestBidAmt3"],
                "bid4_v": json["bestBidAmt4"],
                "bid5_v": json["bestBidAmt5"],
                "ask1_v": json["GAV1"],
                "ask2_v": json["GAV2"],
                "ask3_v": json["GAV3"],
                "ask4_v": json["GAV4"],
                "ask5_v": json["GAV5"],
            })
        except KeyError as e:
            raise HQSourceError(f"行情数据解析失败({e}).")
        return SecurityTicks(**data)
