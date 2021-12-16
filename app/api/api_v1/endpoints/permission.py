"""权限列表的增删查，注意不支持修改，只能删除重新添加"""

from fastapi import APIRouter, Security, Depends, Path, Query, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.errors import NoUserError
from app.core.jwt import get_current_user_authorizer
from app.crud.permission import 获取某用户的所有权限, 获取某角色的权限, 获取某用户的权限, 增加一条权限记录, 删除一条权限记录
from app.crud.user import get_user
from app.db.mongodb import get_database
from app.models.permission import Permission
from app.schema.common import ResultInResponse
from app.schema.permission import 角色权限InRequest

router = APIRouter()


@router.get("", response_model=Permission)
async def get_self_permissions(
    exclude_role: bool = Query(False, description="排除掉用户所具有的角色的权限"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["权限:查看"]),
):
    """获取当前用户自己的所有权限，包括角色和自身赋予的权限"""
    if exclude_role:
        return await 获取某用户的权限(db, user)
    response = await 获取某用户的所有权限(db, user)
    return response


@router.get("/{user_name}", response_model=Permission)
async def query_user_permissions(
    user_name: str = Path(...),
    exclude_role: bool = Query(False, description="排除掉用户所具有的角色的权限"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["权限:查看他人"]),
):
    """获取某用户的所有权限，包括角色和自身赋予的权限"""
    user = await get_user(db, user_name)
    if not user:
        raise NoUserError(message=f"无此用户{user_name}")
    if exclude_role:
        return await 获取某用户的权限(db, user)
    return await 获取某用户的所有权限(db, user)


@router.get("/role/{role_name}", response_model=Permission)
async def query_role_permissions(
    role_name: str = Path(...), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["权限:查看他人"])
):
    """获取某角色的权限"""
    return await 获取某角色的权限(db, role_name)


@router.post("", response_model=Permission)
async def add_a_permission(
    permission: 角色权限InRequest = Body(...), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["权限:创建他人"]),
):
    """增加一条权限"""
    return await 增加一条权限记录(db, permission)


@router.delete("", response_model=ResultInResponse)
async def delete_a_permission(
    permission: 角色权限InRequest = Body(...), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["权限:删除他人"]),
):
    """删除权限"""
    return await 删除一条权限记录(db, permission)
