from app import settings
from app.db.redis import SuperRedis
from app.extentions import logger
from app.global_var import G


async def init_redis_pool():
    """初始化redis"""
    try:
        logger.info("连接redis中...")
        if (
            len(
                {
                    settings.redis.cache_db,
                    settings.redis.entrust_db,
                    settings.redis.portfolio_yield_db,
                }
            )
            != 3
        ):
            logger.error("redis配置错误：redis库不允许重复，请检查配置！")
            return
        # TODO 缓存库 谨慎使用，后期统一规范后再使用
        G.cache = SuperRedis(settings.redis.get_redis_address(settings.redis.cache_db))
        logger.info("连接redis缓存库成功！")
        # 委托订单库
        G.entrust_redis = SuperRedis(
            settings.redis.get_redis_address(settings.redis.entrust_db)
        )
        logger.info("连接redis委托订单库成功！")
        # 组合收益排行库
        G.portfolio_yield_redis = SuperRedis(
            settings.redis.get_redis_address(settings.redis.portfolio_yield_db)
        )
        logger.info("连接redis组合收益排行库成功！")
        # 定时任务临时变量
        G.scheduler_redis = SuperRedis(
            settings.redis.get_redis_address(settings.redis.scheduler_db)
        )
        logger.info("连接redis组合收益排行库成功！")
        # 预加载数据
        G.preload_redis = SuperRedis(
            settings.redis.get_redis_address(settings.redis.preload_db)
        )
        logger.info("连接redis预加载数据库成功！")
    except ConnectionRefusedError as e:
        logger.info(f"连接redis错误：{e}")
        return


async def close_redis():
    """关闭redis"""
    logger.info("关闭redis连接...")
    # # 缓存库
    # await G.cache.close()
    # logger.info("redis缓存库连接关闭！")
    # 委托订单库
    await G.entrust_redis.close()
    logger.info("redis委托订单库连接关闭！")
    # 组合收益排行库
    await G.portfolio_yield_redis.close()
    logger.info("redis组合收益排行库连接关闭！")
    # 定时任务临时变量
    await G.scheduler_redis.close()
    logger.info("redis定时任务临时变量库连接关闭！")
    # 预加载数据
    await G.preload_redis.close()
    logger.info("redis预加载数据连接关闭！")
