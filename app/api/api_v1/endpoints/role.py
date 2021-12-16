"""角色的增删查"""

from typing import List

from fastapi import APIRouter, Security, Depends, Path, Query, Body
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.jwt import get_current_user_authorizer
from app.crud.role import 获取角色列表, 是否角色在数据库中, 增加一个角色, 删除一个角色
from app.db.mongodb import get_database
from app.models.role import Role

router = APIRouter()


@router.get("", response_model=List[Role], description="获取所有角色列表")
async def list_view(
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["角色:查看"]),
):
    return await 获取角色列表(db, limit=limit, skip=skip)


@router.get("/{role_name}", response_model=bool, description="角色是否存在")
async def exist_get_view(
    role_name: str = Path(...), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["角色:查看"])
):
    """获取所有角色"""
    return await 是否角色在数据库中(db, role_name)


@router.post("", response_model=Role, description="创建角色")
async def post_view(role: Role = Body(...), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["角色:创建"])):
    return await 增加一个角色(db, role)


@router.delete("", response_model=bool, description="删除角色")
async def delete_view(role: Role = Body(...), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["角色:删除"])):
    return await 删除一个角色(db, role)
