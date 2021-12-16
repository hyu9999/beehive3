from hq2redis.models import SecurityInfo, SecurityPrice, SecurityHQ, SecurityTicks, SecurityMeta

from app.global_var import G


async def get_security_info(symbol: str, exchange: str) -> SecurityInfo:
    """获取证券基本数据."""
    return await G.hq.get_security_info(symbol, exchange)


async def get_security_price(symbol: str, exchange: str) -> SecurityPrice:
    """获取证券价格数据."""
    return await G.hq.get_security_price(symbol, exchange)


async def get_security_hq(symbol: str, exchange: str) -> SecurityHQ:
    """获取证券行情数据."""
    return await G.hq.get_security_hq(symbol, exchange)


async def get_security_ticks(symbol: str, exchange: str) -> SecurityTicks:
    """获取证券Ticks数据."""
    return await G.hq.get_security_ticks(symbol, exchange)


async def get_security_meta(symbol: str, exchange: str) -> SecurityMeta:
    """获取证券元数据."""
    return await G.hq.get_security_meta(symbol, exchange)
