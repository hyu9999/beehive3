import asyncio

import typer
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.mongodb import db
from app.dec.cmd import typer_log
from app.service.mongodb.clear import clear_mongodb
from app.typer_scripts.utils import init_config

t_app = typer.Typer()

db.client = AsyncIOMotorClient(
    settings.db.MONGODB_URL,
    maxPoolSize=settings.db.MAX_CONNECTIONS,
    minPoolSize=settings.db.MAX_CONNECTIONS,
)
asyncio.get_event_loop().run_until_complete(init_config(db.client))


@t_app.command()
@typer_log
def clear_db(cols: str = None):
    """
    清理数据库垃圾数据

        支持清理的表有： 组合（portfolio）、装备（equipment）、机器人（robot）

    Parameters
    ----------
    col_list  集合列表

    Returns
    -------

    """
    col_list = cols.split(",") if cols else None
    asyncio.get_event_loop().run_until_complete(clear_mongodb(col_list=col_list))


if __name__ == "__main__":
    t_app()
