from datetime import datetime

from hq2redis.models import (
    SecurityHQ,
    SecurityInfo,
    SecurityMeta,
    SecurityPrice,
    SecurityTicks,
)
from hq2redis.utils import get_security_meta

from app.outer_sys.hq.abc import HQSource


class FakeHQ(HQSource):
    @classmethod
    def get_code(cls, symbol: str, exchange: str) -> str:
        ...

    @classmethod
    async def get_security_info(cls, symbol: str, exchange: str) -> SecurityInfo:
        security = await cls.get_security_meta(symbol, exchange)
        return SecurityInfo(
            **security.dict(),
            symbol_name=f"NAME_{symbol}",
            symbol_short_name=f"SHORT_NAME_{symbol}",
            category="stock",
            industry=f"INDUSTRY_{symbol}",
        )

    @classmethod
    async def get_security_price(cls, symbol: str, exchange: str) -> SecurityPrice:
        security = await cls.get_security_meta(symbol, exchange)
        return SecurityPrice(**security.dict(), current=10)

    @classmethod
    async def get_security_hq(cls, symbol: str, exchange: str) -> SecurityHQ:
        security = await cls.get_security_info(symbol, exchange)
        security_meta = await cls.get_security_meta(symbol, exchange)
        security_dict = security.dict()
        security_dict.update(security_meta.dict())
        return SecurityHQ(
            **security_dict,
            current=10,
            date=datetime.today().date(),
            open=5,
            close=10,
            high=20,
            low=5,
            pre_close=5,
        )

    @classmethod
    async def get_security_ticks(cls, symbol: str, exchange: str) -> SecurityTicks:
        """获取证券Ticks数据."""
        security = await cls.get_security_meta(symbol, exchange)
        return SecurityTicks(
            **security.dict(),
            current=10,
            high=20,
            low=5,
            bid1_p=10,
            bid2_p=9,
            bid3_p=8,
            bid4_p=7,
            bid5_p=6,
            ask1_p=10,
            ask2_p=11,
            ask3_p=12,
            ask4_p=13,
            ask5_p=14,
            bid1_v=100,
            bid2_v=100,
            bid3_v=100,
            bid4_v=100,
            bid5_v=100,
            ask1_v=100,
            ask2_v=100,
            ask3_v=100,
            ask4_v=100,
            ask5_v=100,
            ts=datetime.now().timestamp(),
        )

    @classmethod
    async def get_security_meta(cls, symbol: str, exchange: str) -> SecurityMeta:
        """获取证券元数据."""
        meta_data = get_security_meta(symbol)
        meta_data["symbol"] = symbol
        exchange = "SH" if exchange == "1" else "SZ"
        meta_data["exchange"] = exchange
        meta_data["code"] = f"{symbol}.{exchange}"
        return SecurityMeta(**meta_data)
