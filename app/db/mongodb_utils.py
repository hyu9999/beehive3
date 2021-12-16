from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.mongodb import db
from app.extentions import logger


async def get_config(config_name: str) -> str or None:
    return await db.client[settings.db.DB_NAME][
        settings.collections.SITE_CONFIG
    ].find_one({"配置名称": config_name})


async def get_all_configs() -> dict:
    rows = db.client[settings.db.DB_NAME][settings.collections.SITE_CONFIG].find()
    result = {row.pop("配置名称"): row async for row in rows}
    return result


async def connect_to_mongo():
    logger.info("连接数据库中...")
    db.client = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MIN_CONNECTIONS,
    )
    logger.info("连接数据库成功！")


async def load_configuration_from_mongo():
    logger.info("从mongo读取配置中...")
    from app.core.config import set_site_configs

    count = set_site_configs(await get_all_configs())
    logger.info(f"完成{count}条配置!")


async def close_mongo_connection():
    logger.info("关闭数据库连接...")
    db.client.close()
    logger.info("数据库连接关闭！")
