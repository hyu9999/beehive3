import asyncio
import sys
from typing import List

import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.core.discuzq import Discuzq
from app.core.errors import DiscuzqCustomError
from app.crud.discuzq import get_thread, create_thread, get_or_create_disc_user, update_user_signature

sess = aiohttp.ClientSession()

mapping = {
    "robot": {"name": "机器人", "col": settings.collections.ROBOT, "article_id": "文章标识符"},
    "equipment": {"name": "装备", "col": settings.collections.EQUIPMENT, "article_id": "文章标识符"},
    "portfolio": {"name": "组合", "col": settings.collections.PORTFOLIO, "article_id": "article_id"},
}
client = AsyncIOMotorClient(
    settings.db.MONGODB_URL,
    maxPoolSize=settings.db.MAX_CONNECTIONS,
    minPoolSize=settings.db.MIN_CONNECTIONS,
)
db = client.get_database(settings.db.DB_NAME)


async def migrate_user_data():
    """
    migrate user data
    """
    user_col = db.get_collection(settings.collections.USER)
    await Discuzq.admin().login()
    async for user in user_col.find({}):
        try:
            user_id = await get_or_create_disc_user(user["username"][:15])
            # 更新用户签名？？？
            await update_user_signature(
                user_id,
                "nickname" in user and user["nickname"] or "用户{}".format(user["username"][-4:]),
            )
        except DiscuzqCustomError as e:
            print(e.message)
        else:
            if not user.get("disc_id") or user.get("disc_id") != user_id:
                await user_col.update_one({"_id": user["_id"]}, {"$set": {"disc_id": user_id}})
                print("success")


async def migrate_threads_data(map_value):

    cur = db.get_collection(map_value["col"])
    async for obj in cur.find():
        thread_id = obj[map_value["article_id"]] if map_value["article_id"] in obj else None
        # 数据库存在文章id， 并且社区中能查找到相应的文章则跳过
        if thread_id:
            try:
                article = await get_thread(thread_id)
            except Exception as e:
                ...
            else:
                print(f"{'*'*20}{article}")
                if article:
                    continue
        # 创建文章
        res = await create_thread(*await article_params(map_value, obj))
        thread_id = res["id"]
        # 更新beehive3数据库
        await cur.update_one({"_id": obj["_id"]}, {"$set": {"文章标识符": thread_id}})


async def main_func(mapper_list: List[str] = None):
    mapper_list = mapper_list or mapping.keys()
    for mapper in mapper_list:
        print(f"{'*'*20}migrate {mapper}")
        await migrate_threads_data(mapping[mapper])


async def article_params(map_value: dict, obj: dict):
    if map_value["name"] == "组合":
        robot = await db.get_collection(settings.collections.ROBOT).find_one({"标识符": obj["robot"]})
        if robot:
            robot_name = robot["名称"]
        else:
            robot_name = obj["robot"]
        title = (
            f"{obj.get('nickname') or obj['username']}({obj['create_date'].strftime('%Y-%m-%d %H:%M:%S')}) " f"刚刚创建了一个新的组合:{obj['name']} 使用的{robot_name} 机器人."
        )
        data = [
            obj["username"][:15],
            title,
            f"{title}\n{obj['introduction']}",
            settings.discuzq.category[map_value["name"]],
        ]
    else:
        data = [
            obj["作者"][:15],
            f"{map_value['name']}【{obj['名称']}】{obj['创建时间'].strftime('%Y-%m-%d')}创建成功啦",
            f"{map_value['name']}【{obj['名称']}】 创建成功啦\n{obj['简介']}",
            settings.discuzq.category[map_value["name"]],
        ]
    return data


if __name__ == "__main__":
    """

    同步用户|同步社区文章

        * 同步社区文章:支持组合、机器人、装备社区文章的同步

        调用方法
            eg1: 同步用户

            >>poetry run sh -c "PYTHONPATH=. python ./scripts/fill_article_to_discuz.py user"

            eg2: 同步全部社区文章

            >>poetry run sh -c "PYTHONPATH=. python ./scripts/fill_article_to_discuz.py article"
            
            eg3: 同步机器人和装备社区文章

            >>poetry run sh -c "PYTHONPATH=. python ./scripts/fill_article_to_discuz.py article robot,equipment"
            
            eg4: 同步机器人社区文章

            >>poetry run sh -c "PYTHONPATH=. python ./scripts/fill_article_to_discuz.py article robot"
    """
    loop = asyncio.get_event_loop()
    if len(sys.argv) >= 2:
        if sys.argv[1] == "user":
            loop.run_until_complete(migrate_user_data())
        else:
            if len(sys.argv) >= 3:
                loop.run_until_complete(main_func(sys.argv[1].split(",")))
            else:
                loop.run_until_complete(main_func())
    loop.run_until_complete(sess.close())
