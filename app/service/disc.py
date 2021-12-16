import requests
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from app.crud.discuzq import get_thread


async def check_article_exist(article_id):
    return not await get_thread(article_id) is None


async def clear_error_article(conn: AsyncIOMotorClient, collection, filters, name):
    """清理错误的文章id"""
    curs = collection(conn).find(filters)
    bulk_list = []
    async for cur in curs:
        if not check_article_exist(cur[name]):
            bulk_list.append(UpdateOne({"_id": cur["_id"]}, {"$set": {name: None}}))
    if bulk_list:
        await collection(conn).bulk_write(bulk_list)
