import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.crud.discuzq import *

"""
  migrate user data before migrate threads data
  example:
     if __name__ == '__main__':
        asyncio.get_event_loop().run_until_complete(migrate_user_data())
        asyncio.get_event_loop().run_until_complete(migrate_threads_data())
"""

DISCUZ_URL = "https://bbs.jinniuai.com"
DISCUZ_API_KEY = "b7b0ea971e849f0adbd8845981a139fc69df6540a1c1dee741b31201b819a201"  # api key
DISCUZ_CATEGORY = {"10": "组合", "7": "机器人", "5": "装备"}  # category in discuz
sess = aiohttp.ClientSession()


async def register_user(username):
    return await get_or_create_disc_user(username)


async def migrate_user_data():
    """
    migrate user data
    """
    db = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MIN_CONNECTIONS,
    )
    user_col = db.get_database(settings.db.DB_NAME).get_collection(
        settings.collections.USER
    )
    cursor = user_col.find()
    await Discuzq.admin().login()
    async for user in cursor:
        try:
            res = await register_user(user["username"][:15])
            await update_user_signature(
                res,
                "nickname" in user
                and user["nickname"]
                or "用户{}".format(user["username"][-4:]),
            )
            user_col.update_one({"_id": user["_id"]}, {"$set": {"disc_id": res}})
        except DiscuzqCustomError as e:
            print(e.message)


async def move_thread(thread_id):
    """
    migrate thread data
    """
    async with sess.get("{}/t/{}.json".format(DISCUZ_URL, thread_id)) as resp:
        res = await resp.json()
        if not "errors" in res:
            raw = res["post_stream"]["posts"][0]["cooked"]
            title = res["title"]
            category_id = res["category_id"]
            username = res["post_stream"]["posts"][0]["username"]
            res = await create_thread(
                username,
                title,
                raw,
                settings.discuzq.category[DISCUZ_CATEGORY[str(category_id)]],
            )
            return res["id"]
    return thread_id


async def migrate_threads_data():
    db = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MIN_CONNECTIONS,
    )

    equip_col = db.get_database(settings.db.DB_NAME).get_collection(
        settings.collections.EQUIPMENT
    )
    async for equip in equip_col.find():
        thread_id = equip["文章标识符"] if "文章标识符" in equip else None
        if thread_id:
            # get articles from old system
            try:
                new_thread_id = await move_thread(thread_id)
            except Exception as e:
                new_thread_id = thread_id
            equip_col.update_one(
                {"_id": equip["_id"]}, {"$set": {"文章标识符": new_thread_id}}
            )

    portfolio_col = db.get_database(settings.db.DB_NAME).get_collection(
        settings.collections.PORTFOLIO
    )
    async for p in portfolio_col.find():
        thread_id = p["article_id"] if "article_id" in p else None
        if thread_id:
            try:
                new_thread_id = await move_thread(thread_id)
            except Exception as e:
                new_thread_id = thread_id
            portfolio_col.update_one(
                {"_id": p["_id"]}, {"$set": {"article_id": new_thread_id}}
            )

    robot_col = db.get_database(settings.db.DB_NAME).get_collection(
        settings.collections.ROBOT
    )
    async for robot in robot_col.find():
        thread_id = robot["文章标识符"] if "文章标识符" in robot else None
        if thread_id:
            try:
                new_thread_id = await move_thread(thread_id)
            except Exception as e:
                new_thread_id = thread_id
            robot_col.update_one(
                {"_id": robot["_id"]}, {"$set": {"文章标识符": new_thread_id}}
            )
