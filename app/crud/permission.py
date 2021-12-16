from typing import Union

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.errors import PermissionAlreadyExist, RoleAlreadyExist, PermissionDoesNotExist
from app.core.utils import merge_two_dicts
from app.crud.base import get_permissions_collection
from app.crud.role import 是否角色在数据库中
from app.extentions import logger
from app.models.permission import Permission
from app.models.user import User as UserInDB
from app.schema.common import ResultInResponse
from app.schema.permission import 角色权限InRequest
from app.schema.user import User


async def 获取某角色的权限(conn: AsyncIOMotorClient, role: str) -> Permission:
    """获取某角色的所有权限。不论有多少条记录，返回会合并成为一个权限字典。"""
    permissions = get_permissions_collection(conn).find({"role": role})
    response = Permission(role=role, permissions={})
    async for permission in permissions:
        response.permissions = merge_two_dicts(permission["permissions"], response.permissions)
    return response


async def 获取某用户的权限(conn: AsyncIOMotorClient, user: Union[User, UserInDB]) -> Permission:
    """ 获取某用户的权限(不包含用户拥有的角色名下的)。不论有多少条记录，返回会合并成为一个权限字典。 """
    permissions = get_permissions_collection(conn).find({"role": {"$in": user.roles}})
    response = Permission(permissions={})
    async for permission in permissions:
        response.permissions = merge_two_dicts(permission["permissions"], response.permissions)
    return response


async def 获取某用户的所有权限(conn: AsyncIOMotorClient, user: Union[User, UserInDB]) -> Permission:
    """ 获取某用户自己名下的和拥有的角色名下的所有权限，并且不论有多少条记录，返回会合并成为一个权限字典。"""
    response = Permission(permissions={})
    if user.roles:
        for role in user.roles:
            permission = await 获取某角色的权限(conn, role)
            response.permissions = merge_two_dicts(permission.permissions, response.permissions)
    return response


async def 增加一条权限记录(conn: AsyncIOMotorClient, permission: Union[角色权限InRequest]) -> Permission:
    result = await get_permissions_collection(conn).find_one({"role": permission.role})
    if result:
        logger.error(f"该角色（{permission.role}）已有一条权限记录，请删除后再试或者尝试修改记录")
        raise PermissionAlreadyExist(message=f"该角色（{permission.role}）已有一条权限记录，请删除后再试或者尝试修改记录")
    result = await 是否角色在数据库中(conn, permission.role)
    if not result:
        logger.error(f"该角色（{permission.role}）不是一条合法的角色，请检查角色列表")
        raise RoleAlreadyExist(message=f"该角色（{permission.role}）不是一条合法的角色，请检查角色列表")

    await get_permissions_collection(conn).insert_one(permission.dict())
    return Permission(**permission.dict())


async def 删除一条权限记录(conn: AsyncIOMotorClient, permission: Union[角色权限InRequest]) -> ResultInResponse:
    result = await get_permissions_collection(conn).find_one({"role": permission.role})
    if not result:
        logger.error(f"该角色（{permission.role}）没有权限记录")
        raise PermissionDoesNotExist
    await get_permissions_collection(conn).delete_one({"_id": result["_id"]})
    return ResultInResponse()
