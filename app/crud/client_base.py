from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCursor

from app.core.errors import ClientPermissionDenied
from app.crud.base import get_robots_collection, get_equipment_collection
from app.schema.user import User


async def permission_db_query(db_query: dict, collection_name: str, user: User = None):
    """过滤db_query中标识符字段"""
    if user and "厂商用户" in user.roles:
        sid_query = {"$or": [{"标识符": {"$in": user.client.__dict__[collection_name]}}, {"作者": user.username}]}
        query = db_query.copy()
        if "标识符" in query.keys():
            if isinstance(query["标识符"], str) and query["标识符"] not in user.client.__dict__[collection_name]:
                raise ClientPermissionDenied(message=f"没有该{collection_name}[{query['标识符']}]的使用权限")
            elif isinstance(query["标识符"], dict) and len(query["标识符"]["$in"]) > 0:
                sid_intersection = list(set(query["标识符"]["$in"]) & set(user.client.__dict__[collection_name]))
                if not sid_intersection:
                    raise ClientPermissionDenied(message=f"没有该{collection_name}[{query['标识符']}]的使用权限")
                else:
                    sid_query = {"标识符": {"$in": sid_intersection}}
        return {"$and": [query, sid_query]}
    return db_query


async def get_client_equipment_cursor(
    conn: AsyncIOMotorClient, db_query: dict, limit: int = 20, skip: int = 0, sort: list = None, user: User = None
) -> AsyncIOMotorCursor:
    permission_query = await permission_db_query(db_query, "equipment", user)
    list_cursor = get_equipment_collection(conn).find(permission_query, limit=limit, skip=skip, sort=sort)
    return list_cursor


async def get_client_equipment_count(conn: AsyncIOMotorClient, query: dict, user: User = None) -> int:
    db_query = {key: value for key, value in query.items() if value}
    permission_query = await permission_db_query(db_query, "equipment", user)
    return await get_equipment_collection(conn).count_documents(permission_query)


async def get_client_robot_cursor(
    conn: AsyncIOMotorClient, db_query: dict, limit: int = 20, skip: int = 0, sort: list = None, user: User = None
) -> AsyncIOMotorCursor:
    permission_query = await permission_db_query(db_query, "robot", user)
    list_cursor = get_robots_collection(conn).find(permission_query, limit=limit, skip=skip, sort=sort)
    return list_cursor


async def get_client_robot_count(conn: AsyncIOMotorClient, query: dict, user: User = None) -> int:
    db_query = {key: value for key, value in query.items() if value}
    permission_query = await permission_db_query(db_query, "robot", user)
    return await get_robots_collection(conn).count_documents(permission_query)


async def get_client_robot_list(conn: AsyncIOMotorClient, query: dict, user: User = None):
    query.update({"状态": "已上线", "评级": {"$in": ["A", "B", "C"]}})
    return [row async for row in await get_client_robot_cursor(conn, query, sort=[("累计服务人数", -1)], user=user)]
