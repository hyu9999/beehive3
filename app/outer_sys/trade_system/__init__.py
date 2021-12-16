from app import settings
from app.extentions import logger
from app.global_var import G
from app.outer_sys.trade_system.pt.pt_trade_adaptor import PTAdaptor
from app.outer_sys.trade_system.trade_interface import TradeInterface


async def connect_trade_system():
    if settings.trade_url is not None:
        trade_adaptor = PTAdaptor(settings.trade_url)
        G.trade_system = TradeInterface(trade_adaptor)
        logger.info("交易系统连接成功.")
    else:
        logger.info("交易系统连接失败，请设置TRADE_URL.")


async def close_trade_system():
    await G.trade_system.close()
