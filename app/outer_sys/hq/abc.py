from abc import ABCMeta, abstractmethod

from hq2redis.models import SecurityInfo, SecurityPrice, SecurityHQ, SecurityTicks, SecurityMeta
from hq2redis.utils import get_security_meta


class HQSource(metaclass=ABCMeta):
    HQ2REDIS_EXCHANGE_MAPPING = {"0": "SZ", "1": "SH"}
    @classmethod
    @abstractmethod
    def get_code(cls, symbol: str, exchange: str) -> str:
        """获取证券代码."""

    @classmethod
    @abstractmethod
    async def get_security_info(cls, symbol: str, exchange: str) -> SecurityInfo:
        """获取证券基本信息数据."""

    @classmethod
    @abstractmethod
    async def get_security_price(cls, symbol: str, exchange: str) -> SecurityPrice:
        """获取证券价格数据."""

    @classmethod
    @abstractmethod
    async def get_security_hq(cls, symbol: str, exchange: str) -> SecurityHQ:
        """获取证券行情数据."""

    @classmethod
    @abstractmethod
    async def get_security_ticks(cls, symbol: str, exchange: str) -> SecurityTicks:
        """获取证券Ticks数据."""

    @classmethod
    async def get_security_meta(cls, symbol: str, exchange: str) -> SecurityMeta:
        """获取证券元数据."""
        meta = get_security_meta(cls._get_hq2redis_code(symbol, exchange))
        return SecurityMeta(symbol=symbol, exchange=cls.HQ2REDIS_EXCHANGE_MAPPING[exchange], **meta)

    @classmethod
    def _get_hq2redis_code(cls, symbol: str, exchange: str):
        return f"{symbol}.{cls.HQ2REDIS_EXCHANGE_MAPPING[exchange]}"
