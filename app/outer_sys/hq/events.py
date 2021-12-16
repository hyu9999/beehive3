from hq2redis import HQ2Redis
from hq2redis.enums import QuotesSourceEnum

from app import settings
from app.extentions import logger
from app.global_var import G
from app.outer_sys.hq.constant import HQ_SOURCE_MAPPING


async def set_hq_source():
    """配置行情源."""
    logger.info("正在配置行情源...")
    hq_source = settings.hq.source
    if hq_source not in HQ_SOURCE_MAPPING.keys():
        raise ValueError("请配置可用的行情源(Jiantou/Redis).")
    G.hq = HQ_SOURCE_MAPPING[hq_source]()
    logger.info("配置行情源完成.")


async def connect_hq2reids():
    logger.info("正在连接HQ2Redis...")
    hq2redis = HQ2Redis(
        redis_host=settings.redis.hq2redis_host,
        redis_port=settings.redis.hq2redis_port,
        redis_db=settings.redis.hq2redis_db,
        redis_password=settings.redis.hq2redis_password,
    )
    await hq2redis.startup()
    G.hq2redis = hq2redis
    logger.info("连接HQ2Redis连接完成.")


async def close_hq2redis_conn():
    logger.info("正在关闭行情HQ2Redis连接...")
    await G.hq2redis.shutdown()
    logger.info("HQ2Redis连接已关闭.")
