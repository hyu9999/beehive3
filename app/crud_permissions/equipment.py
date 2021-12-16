from fastapi import Security, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.status import HTTP_403_FORBIDDEN

from app.crud.base import get_equipment_collection
from app.crud_permissions.base import get_user_scopes


async def 是否有修改装备权限(sid: str, user: Security, db: AsyncIOMotorClient):
    scopes = await get_user_scopes(db, user)
    if "装备:修改他人" in scopes or ".*:.*" in scopes:
        return True
    result = await get_equipment_collection(db).find_one({"标识符": sid, "作者": user.username})
    if result:
        return True
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"您没有修改该装备（{sid}）的权限")


async def 是否有删除装备权限(sid: str, user: Security, db: AsyncIOMotorClient):
    scopes = await get_user_scopes(db, user)
    if "装备:删除他人" in scopes or ".*:.*" in scopes:
        return True
    result = await get_equipment_collection(db).find_one({"标识符": sid, "作者": user.username})
    if result:
        return True
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"您没有删除该装备（{sid}）的权限")
