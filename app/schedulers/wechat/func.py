from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

from app.crud.base import get_user_collection
from app.db.mongodb import db
from app.outer_sys.wechat.user import get_wechat_avatar


async def sync_wechat_avatar_task(conn=None):
    """
    同步微信头像
    """
    conn = db.client or conn
    bulk_data = [
        UpdateOne({"_id": x["_id"]}, {"$set": {"avatar": get_wechat_avatar(x["open_id"])}})
        async for x in get_user_collection(conn).find({"$and": [{"open_id": {"$exists": True}}, {"open_id": {"$nin": ["", None]}}]})
    ]
    await get_user_collection(conn).bulk_write(bulk_data) if bulk_data else False
