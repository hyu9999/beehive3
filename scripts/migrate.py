import asyncio
import logging
import os
import sys

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from pymongo.errors import CollectionInvalid

from app import settings
from app.settings.db import db_idx

sys.path.append(os.path.dirname(__file__) + os.sep + "../")

logger = logging.getLogger("migrate")
logger.setLevel(logging.INFO)


async def create_collection(db: AsyncIOMotorDatabase, name: str):
    try:
        await db.create_collection(name)
    except CollectionInvalid as e:
        logger.info(e)
    else:
        logger.info(f"创建集合({name})成功\n")


async def migrate(col_name: str = None):
    db = AsyncIOMotorClient(settings.db.MONGODB_URL, maxPoolSize=settings.db.MAX_CONNECTIONS, minPoolSize=settings.db.MIN_CONNECTIONS)
    cols = settings.collections.dict()
    if col_name:
        col_name = col_name.lower()
        if col_name not in cols.values():
            raise KeyError(f"该集合({col_name})未定义")
        cols = {col_name.upper(): col_name}
    for k, col_name in cols.items():
        await create_collection(db[settings.db.DB_NAME], col_name)
        logging.warning(f"创建集合({col_name})成功")
        idx_list = db_idx.__dict__.get(f"{col_name.upper()}_IDX", [])
        for idx, unique in idx_list:
            result = await db[settings.db.DB_NAME][col_name].create_index(idx, unique=unique)
            logger.info(f"创建({result})索引成功。\n")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if len(sys.argv) >= 2:
        loop.run_until_complete(migrate(sys.argv[1]))
    else:
        loop.run_until_complete(migrate())
