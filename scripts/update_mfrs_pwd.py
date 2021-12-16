import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings


async def update_mfrs_password():
    db = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MIN_CONNECTIONS,
    )
    user_col = db.get_database(settings.db.DB_NAME).get_collection(settings.collections.USER)
    cursor = user_col.find({"roles": "厂商用户"})
    async for user in cursor:
        user_col.update_one({"_id": user["_id"]}, {"$set": {"hashed_password": user["app_secret"]}})


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_mfrs_password())
