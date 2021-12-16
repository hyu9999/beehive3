from fastapi import Security, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.status import HTTP_403_FORBIDDEN

from app.crud.base import get_robots_collection
from app.crud_permissions.base import get_user_scopes


async def 是否有修改机器人权限(sid: str, user: Security, db: AsyncIOMotorClient):
    scopes = await get_user_scopes(db, user)
    if "机器人:修改他人" in scopes or ".*:.*" in scopes:
        return True
    result = await get_robots_collection(db).find_one({"标识符": sid, "作者": user.username})
    if result:
        return True
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"您没有修改该机器人（{sid}）的权限")


async def 是否有删除机器人权限(sid: str, user: Security, db: AsyncIOMotorClient):
    scopes = await get_user_scopes(db, user)
    if "机器人:删除他人" in scopes or ".*:.*" in scopes:
        return True
    result = await get_robots_collection(db).find_one({"标识符": sid, "作者": user.username})
    if result:
        return True
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"您没有删除该机器人（{sid}）的权限")
