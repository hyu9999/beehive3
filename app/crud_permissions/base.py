from fastapi import Security
from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.permission import 获取某用户的所有权限


async def get_user_scopes(db: AsyncIOMotorClient, user: Security):
    user_permissions = await 获取某用户的所有权限(db, user)
    return [":".join([key, value]).replace("*", ".*") for key in user_permissions.permissions for value in user_permissions.permissions[key]]
