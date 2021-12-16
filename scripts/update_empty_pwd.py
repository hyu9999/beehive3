import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.core.security import generate_salt, get_password_hash


async def update_empty_password(default_pwd):
    """
    更新密码为空的用户（不包含微信用户）

    Parameters
    ----------
    default_pwd

    Returns
    -------

    """
    db = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MIN_CONNECTIONS,
    )
    user_col = db.get_database(settings.db.DB_NAME).get_collection(settings.collections.USER)
    cursor = user_col.find({"$or": [{"hashed_password": {"$exists": False}}, {"hashed_password": None}], "open_id": None})
    async for user in cursor:
        salt = generate_salt()
        hashed_password = get_password_hash(salt + default_pwd)
        user_col.update_one({"_id": user["_id"]}, {"$set": {"hashed_password": hashed_password, "salt": salt}})


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_empty_password("666666"))
