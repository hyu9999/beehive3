from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_roles_collection
from app.models.role import Role


async def 获取角色列表(conn: AsyncIOMotorClient, limit: int, skip: int) -> List[Role]:
    """获取所有角色"""
    roles = get_roles_collection(conn).find({}, skip=skip, limit=limit)
    return [Role(**role) async for role in roles]


async def 是否角色在数据库中(conn: AsyncIOMotorClient, role_name: str) -> bool:
    """检查某个角色是否在数据库中"""
    role = await get_roles_collection(conn).find_one({"name": role_name})
    if role:
        return True
    else:
        return False


async def 增加一个角色(conn: AsyncIOMotorClient, role: Role) -> Role:
    result = await get_roles_collection(conn).insert_one(role.dict())
    if result:
        return role


async def 删除一个角色(conn: AsyncIOMotorClient, role: Role) -> bool:
    result = await get_roles_collection(conn).delete_one(role.dict())
    if result.deleted_count > 0:
        return True
    else:
        return False
