from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.core.config import set_site_configs


async def init_config(conn: AsyncIOMotorClient):
    rows = conn[settings.db.DB_NAME][settings.collections.SITE_CONFIG].find()
    set_site_configs({row.pop("配置名称"): row async for row in rows})
