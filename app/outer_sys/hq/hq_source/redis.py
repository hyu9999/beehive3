from hq2redis.models import SecurityInfo, SecurityPrice, SecurityHQ, SecurityTicks, SecurityMeta
from hq2redis.reader import get_security_info, get_security_price, get_security_hq, get_security_ticks, \
    get_security_meta

from app.outer_sys.hq.abc import HQSource


class RedisHQ(HQSource):
    EXCHANGE_MAPPING = {"0": "SZ", "1": "SH"}
    @classmethod
    def get_code(cls, symbol: str, exchange: str) -> str:
        """获取证券代码."""
        return f"{symbol}.{cls.EXCHANGE_MAPPING[exchange]}"

    @classmethod
    async def get_security_info(cls, symbol: str, exchange: str) -> SecurityInfo:
        """获取证券基本信息数据."""
        return await get_security_info(cls.get_code(symbol, exchange))

    @classmethod
    async def get_security_price(cls, symbol: str, exchange: str) -> SecurityPrice:
        """获取证券价格数据."""
        return await get_security_price(cls.get_code(symbol, exchange))

    @classmethod
    async def get_security_hq(cls, symbol: str, exchange: str) -> SecurityHQ:
        """获取证券行情数据."""
        return await get_security_hq(cls.get_code(symbol, exchange))

    @classmethod
    async def get_security_ticks(cls, symbol: str, exchange: str) -> SecurityTicks:
        """获取证券Ticks数据."""
        return await get_security_ticks(cls.get_code(symbol, exchange))

    @classmethod
    async def get_security_meta(cls, symbol: str, exchange: str) -> SecurityMeta:
        """获取证券元数据."""
        return await get_security_meta(cls.get_code(symbol, exchange))
