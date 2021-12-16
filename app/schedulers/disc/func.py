from typing import Dict, List

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError

from app import settings
from app.core.errors import DiscuzqCustomError
from app.crud.base import (
    get_equipment_collection,
    get_portfolio_collection,
    get_robots_collection,
    get_user_collection,
)
from app.crud.discuzq import (
    create_thread,
    get_or_create_disc_user,
    update_user_signature,
)
from app.db.mongodb import db
from app.extentions import logger
from app.schema.user import User
from app.service.disc import clear_error_article


async def fill_disc_user(conn: AsyncIOMotorClient, filters: Dict = None):
    """
    将社区用户id刷到用户表的字段disc_id中
    Returns
    -------

    """
    logger.info("将社区用户id刷到用户表的字段disc_id中")
    filters = filters or {}
    # 将无效的文章id置为空
    error_filters = {"disc_id": {"$exists": True}}
    error_filters.update(filters)
    await clear_error_article(conn, get_user_collection, error_filters, "disc_id")
    #
    filters.update({"$or": [{"disc_id": {"$exists": False}}, {"disc_id": None}]})
    missing_data = get_user_collection(conn).find(filters)
    async for user in missing_data:
        user["id"] = user["_id"]
        user["nickname"] = user.get("nickname") or f"用户{user['username'][-4:]}"
        user["email"] = (
            user.get("email")
            or f"disc_{user['mobile'] or user['username']}@discourse.com"
        )
        user["password"] = f"{user['mobile'] or user['username']}@abcdefg"
        try:
            disc_id = await get_or_create_disc_user(user["username"], User(**user))
            await update_user_signature(disc_id, user["nickname"])
        except DiscuzqCustomError as e:
            logger.error(f"创建社区用户({user['username']})失败：{e.message}")
        except ValidationError as e:
            logger.error(f"创建社区用户({user['username']})失败：{e}")
        else:
            await get_user_collection(conn).update_one(
                {"username": user["username"]}, {"$set": {"disc_id": disc_id}}
            )


async def fill_disc_article_to_portfolio(
    conn: AsyncIOMotorClient, filters: Dict = None
):
    """
    将社区文章id刷到组合表的字段article_id中
    Returns
    -------

    """
    logger.info("将社区文章id刷到组合表的字段article_id中")
    filters = filters or {}
    # 将无效的文章id置为空
    error_filters = {"article_id": {"$exists": True}}
    error_filters.update(filters)
    await clear_error_article(
        conn, get_portfolio_collection, error_filters, "article_id"
    )
    #
    filters.update(
        {
            "status": "running",
            "$or": [{"article_id": {"$exists": False}}, {"article_id": None}],
        }
    )
    missing_data = get_portfolio_collection(conn).find(filters)
    async for x in missing_data:
        title = (
            f"{x['username']}({x['create_date'].strftime('%Y-%m-%d %H:%M:%S')}) "
            f"刚刚创建了一个新的组合:{x['name']} 使用的{x['robot']} 机器人"
        )
        data = {
            "title": title,
            "raw": f"{title}\n{x['introduction']}",
            "category": settings.discuzq.category["组合"],
        }
        try:
            article = await create_thread(x["username"], **data)
        except DiscuzqCustomError as e:
            logger.error(f"创建组合社区文章({x['username']}-{x['_id']})失败：{e.message}")
        else:
            await get_portfolio_collection(conn).update_one(
                {"_id": x["_id"]}, {"$set": {"article_id": article["id"]}}
            )


async def fill_disc_article_to_equipment(
    conn: AsyncIOMotorClient, filters: Dict = None
):
    """
    将社区文章id刷到装备表的字段"文章标识符"中
    Returns
    -------

    """
    logger.info("将社区文章id刷到装备表的字段“文章标识符”中")
    filters = filters or {}
    error_filters = {"文章标识符": {"$exists": True}}
    error_filters.update(filters)
    await clear_error_article(conn, get_equipment_collection, error_filters, "文章标识符")
    filters.update(
        {"状态": {"$ne": "已删除"}, "$or": [{"文章标识符": {"$exists": False}}, {"文章标识符": None}]}
    )
    missing_data = get_equipment_collection(conn).find(filters)
    async for x in missing_data:
        topic = {
            "title": f"装备【{x['名称']}】{x['创建时间'].strftime('%Y-%m-%d')}上线啦",
            "raw": f"装备【{x['名称']}】 创建成功啦\n{x['简介']}",
            "category": settings.discuzq.category["装备"],
        }
        try:
            obj = await create_thread(x["作者"], **topic)
        except DiscuzqCustomError as e:
            logger.error(f"[发布文章({x['标识符']})失败] {e.message}")
        else:
            # 更新装备中的字段
            await get_equipment_collection(conn).update_one(
                {"标识符": x["标识符"]}, {"$set": {"文章标识符": obj["id"]}}
            )


async def fill_disc_article_to_robot(conn: AsyncIOMotorClient, filters: Dict = None):
    """
    将社区文章id刷到机器人表的字段"文章标识符"中
    Returns
    -------

    """
    logger.info("将社区文章id刷到机器人表的字段“文章标识符”中")
    filters = filters or {}
    error_filters = {"文章标识符": {"$exists": True}}
    error_filters.update(filters)
    await clear_error_article(conn, get_robots_collection, error_filters, "文章标识符")
    filters.update(
        {
            "状态": {"$in": ["已上线", "已下线"]},
            "$or": [{"文章标识符": {"$exists": False}}, {"文章标识符": None}],
        }
    )
    missing_data = get_robots_collection(conn).find(filters)
    async for x in missing_data:
        topic = {
            "title": f"机器人【{x['名称']}】{x['创建时间'].strftime('%Y-%m-%d')}创建成功啦",
            "raw": f"机器人【{x['名称']}】 创建成功啦\n{x['简介']}",
            "category": settings.discuzq.category["机器人"],
        }
        try:
            obj = await create_thread(x["作者"], **topic)
        except DiscuzqCustomError as e:
            logger.error(f"[发布文章({x['标识符']})失败]{e.message}")
        else:
            # 更新装备中的字段
            await get_robots_collection(conn).update_one(
                {"标识符": x["标识符"]}, {"$set": {"文章标识符": obj["id"]}}
            )


DATA_LIST = {
    "user": fill_disc_user,
    "portfolio": fill_disc_article_to_portfolio,
    "equipment": fill_disc_article_to_equipment,
    "robot": fill_disc_article_to_robot,
}


async def fill_disc_data(conn: AsyncIOMotorClient = None, data_list: List = None):
    """
    补充社区数据
    Returns
    -------

    """
    conn = conn or db.client
    data_list = data_list or DATA_LIST
    for x in data_list:
        await DATA_LIST[x](conn)
