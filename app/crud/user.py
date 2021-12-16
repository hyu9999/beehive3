import math
from datetime import datetime
from typing import List, Optional, Union

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import EmailStr

from app import settings
from app.core.config import get
from app.core.errors import CRUDError, NoUserError, TableFieldError
from app.crud.base import (
    get_equipment_collection,
    get_portfolio_collection,
    get_robots_collection,
    get_user_collection,
    get_user_message_collection,
)
from app.crud.discuzq import get_or_create_disc_user, update_user_signature
from app.enums.user import 消息分类, 消息类型
from app.models.base.user import 厂商基本信息
from app.models.equipment import Equipment
from app.models.portfolio import Portfolio
from app.models.robot import Robot
from app.models.user import User
from app.schema.common import KeyValueInResponse, ResultInResponse
from app.schema.user import (
    ManufacturerUserInCreate,
    ManufacturerUserInUpdate,
    UserInCreate,
    UserInUpdate,
    UserInUpdatePwd,
    UserMessageInCreate,
    UserMessageListInResponse,
    UserMessagenInResponse,
)


async def get_user(conn: AsyncIOMotorClient, username: str) -> User:
    row = await get_user_collection(conn).find_one({"username": username})
    if row:
        return User(**row)


async def get_user_by_email(conn: AsyncIOMotorClient, email: EmailStr) -> User:
    row = await get_user_collection(conn).find_one({"email": email})
    if row:
        return User(**row)


async def get_user_by_mobile(conn: AsyncIOMotorClient, mobile: str) -> User:
    row = await get_user_collection(conn).find_one({"mobile": mobile})
    if row:
        return User(**row)


async def get_user_by_username(conn: AsyncIOMotorClient, username: str) -> User:
    row = await get_user_collection(conn).find_one({"username": username})
    if row:
        return User(**row)


async def get_user_by_nickname(conn: AsyncIOMotorClient, nickname: Union[str, List[str]]) -> List[User]:
    query = {"nickname": nickname} if isinstance(nickname, str) else {"nickname": {"$in": nickname}}
    cursor = get_user_collection(conn).find(query)
    return [User(**row) async for row in cursor]


async def get_manufacturer_user(conn: AsyncIOMotorClient, username: str = None) -> List[User]:
    query = {"roles": "厂商用户"}
    if username:
        query["username"] = username
    cursor = get_user_collection(conn).find(query)
    return [User(**row) async for row in cursor]


async def create_user(conn: AsyncIOMotorClient, user: UserInCreate, roles=()) -> User:
    dbuser = User(**user.dict())
    dbuser.change_password(user.password)
    if roles:
        dbuser.roles = []
        dbuser.roles.append(roles)
    else:
        dbuser.roles = [get("新注册用户的初始角色")]
    # 注册社区
    disc_id = await get_or_create_disc_user(dbuser.username)
    await update_user_signature(
        disc_id,
        dbuser.nickname and dbuser.nickname or "用户{}".format(dbuser.username[-4:]),
    )
    dbuser.disc_id = disc_id
    row = await get_user_collection(conn).insert_one(dbuser.dict(exclude={"id"}))

    dbuser.id = row.inserted_id

    return dbuser


async def delete_user(conn: AsyncIOMotorClient, username: str):
    result = await get_user_collection(conn).delete_one({"username": username})
    if result.deleted_count == 0:
        raise NoUserError(message="用户不存在或者已经删除")


async def delete_manufacturer_user(conn: AsyncIOMotorClient, username: str):
    result = await get_user_collection(conn).delete_one({"username": username})
    if result.deleted_count == 0:
        raise NoUserError(message="用户不存在或者已经删除")


async def update_manufacturer_user(conn: AsyncIOMotorClient, username: str, data: KeyValueInResponse) -> User:
    if data.name.startswith("client."):
        if data.name.split(".")[-1] not in 厂商基本信息().dict().keys():
            raise TableFieldError()
    else:
        if data.name in ["username", "mobile"]:
            raise TableFieldError(message="存在不允许修改的字段")
        if data.name not in ManufacturerUserInUpdate().dict().keys():
            raise TableFieldError()
    updated_result = await get_user_collection(conn).update_one({"username": username}, {"$set": {f"{data.name}": data.value}})
    if not updated_result.matched_count:
        raise CRUDError(message=f"更新用户文档错误，错误内容：{updated_result}")
    return await get_user(conn, username)


async def update_user(conn: AsyncIOMotorClient, username: str, user: UserInUpdate) -> User:
    params = user.dict(exclude_defaults=True)
    if params:
        updated_result = await get_user_collection(conn).update_one({"username": username}, {"$set": params})
        if not updated_result.matched_count:
            raise CRUDError(message=f"更新用户文档错误，错误内容：{updated_result}")
    return await get_user(conn, username)


async def create_manufacturer_user(conn: AsyncIOMotorClient, user: ManufacturerUserInCreate, roles=()) -> User:
    dbuser = User(**user.dict())
    dbuser.client.indicator = settings.mfrs.CLIENT_INDICATOR
    dbuser.nickname = dbuser.client_name
    dbuser.change_password(user.app_secret)
    dbuser.change_app_secret(user.app_secret)
    if roles:
        dbuser.roles = []
        dbuser.roles.append(roles)
    else:
        dbuser.roles = ["厂商用户"]
    # 注册社区
    disc_id = await get_or_create_disc_user(dbuser.username)
    await update_user_signature(
        disc_id,
        dbuser.nickname and dbuser.nickname or "用户{}".format(dbuser.username[-4:]),
    )
    dbuser.disc_id = disc_id
    row = await get_user_collection(conn).insert_one(dbuser.dict(exclude={"id"}))

    dbuser.id = row.inserted_id
    return dbuser


async def update_pwd(conn: AsyncIOMotorClient, password: str, dbuser: User):
    dbuser.change_password(password)
    updated_result = await get_user_collection(conn).update_one({"username": dbuser.username}, {"$set": dbuser.dict()})
    if updated_result.matched_count == updated_result.modified_count == 1:
        return dbuser


async def update_app_secret(conn: AsyncIOMotorClient, app_secret: str, dbuser: User):
    dbuser.change_app_secret(app_secret)
    updated_result = await get_user_collection(conn).update_one({"username": dbuser.username}, {"$set": {"app_secret": app_secret}})
    if updated_result.matched_count == updated_result.modified_count == 1:
        return dbuser


async def 订阅装备(conn: AsyncIOMotorClient, user: User, equipment: Equipment):
    if equipment.标识符 in user.equipment.subscribe_info.focus_list:
        return ResultInResponse()
    user.equipment.subscribe_info.focus_list.append(equipment.标识符)
    user.equipment.subscribe_info.focus_num += 1
    async with await conn.start_session() as s:
        async with s.start_transaction():
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"equipment.subscribe_info": user.equipment.subscribe_info.dict()}},
            )
            await get_user_collection(conn).update_one(
                {"username": equipment.作者},
                {"$inc": {"equipment.subscribe_info.fans_num": 1}},
            )
            订阅人数 = equipment.订阅人数 + 1
            await get_equipment_collection(conn).update_one({"标识符": equipment.标识符}, {"$set": {"订阅人数": 订阅人数}})
            message = {
                "title": "订阅装备",
                "content": f"您已成功订阅了“{equipment.名称}”",
                "category": 消息分类.equipment,
                "msg_type": 消息类型.subscribe,
                "data_info": equipment.标识符,
                "username": user.username,
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
            return ResultInResponse()


async def 取消订阅装备(conn: AsyncIOMotorClient, user: User, equipment: Equipment):
    if equipment.标识符 not in user.equipment.subscribe_info.focus_list:
        return ResultInResponse()
    user.equipment.subscribe_info.focus_list.remove(equipment.标识符)
    user.equipment.subscribe_info.focus_num -= 1
    async with await conn.start_session() as s:
        async with s.start_transaction():
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"equipment.subscribe_info": user.equipment.subscribe_info.dict()}},
            )
            await get_user_collection(conn).update_one(
                {"username": equipment.作者},
                {"$inc": {"equipment.subscribe_info.fans_num": -1}},
            )
            订阅人数 = equipment.订阅人数 - 1 if equipment.订阅人数 > 0 else 0
            await get_equipment_collection(conn).update_one({"标识符": equipment.标识符}, {"$set": {"订阅人数": 订阅人数}})
            return ResultInResponse()


async def 订阅机器人(conn: AsyncIOMotorClient, user: User, robot: Robot):
    if robot.标识符 in user.robot.subscribe_info.focus_list:
        return ResultInResponse()
    user.robot.subscribe_info.focus_list.append(robot.标识符)
    user.robot.subscribe_info.focus_num += 1
    async with await conn.start_session() as s:
        async with s.start_transaction():
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"robot.subscribe_info": user.robot.subscribe_info.dict()}},
            )
            await get_user_collection(conn).update_one({"username": robot.作者}, {"$inc": {"robot.subscribe_info.fans_num": 1}})
            订阅人数 = robot.订阅人数 + 1
            await get_robots_collection(conn).update_one({"标识符": robot.标识符}, {"$set": {"订阅人数": 订阅人数}})
            message = {
                "title": "订阅机器人",
                "content": f"您已成功订阅了“{robot.名称}”",
                "category": 消息分类.robot,
                "msg_type": 消息类型.subscribe,
                "data_info": robot.标识符,
                "username": user.username,
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
            return ResultInResponse()


async def 取消订阅机器人(conn: AsyncIOMotorClient, user: User, robot: Robot):
    if robot.标识符 not in user.robot.subscribe_info.focus_list:
        return ResultInResponse()
    user.robot.subscribe_info.focus_list.remove(robot.标识符)
    user.robot.subscribe_info.focus_num -= 1
    async with await conn.start_session() as s:
        async with s.start_transaction():
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"robot.subscribe_info": user.robot.subscribe_info.dict()}},
            )
            await get_user_collection(conn).update_one({"username": robot.作者}, {"$inc": {"robot.subscribe_info.fans_num": -1}})
            订阅人数 = robot.订阅人数 - 1 if robot.订阅人数 > 0 else 0
            await get_robots_collection(conn).update_one({"标识符": robot.标识符}, {"$set": {"订阅人数": 订阅人数}})
            return ResultInResponse()


async def subscribe_portfolio(conn: AsyncIOMotorClient, user: User, portfolio: Portfolio):
    if portfolio.id in user.portfolio.subscribe_info.focus_list:
        return ResultInResponse()
    user.portfolio.subscribe_info.focus_list.append(portfolio.id)
    user.portfolio.subscribe_info.focus_num += 1
    async with await conn.start_session() as s:
        async with s.start_transaction():
            # 更新用户subscribe_info中的订阅列表和订阅数量，同时被关注者粉丝数量+1，组合数据订阅数量+1
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"portfolio.subscribe_info": user.portfolio.subscribe_info.dict()}},
            )
            await get_user_collection(conn).update_one(
                {"username": portfolio.username},
                {"$inc": {"portfolio.subscribe_info.fans_num": 1}},
            )
            subscribe_num = portfolio.subscribe_num + 1
            subscribers = portfolio.subscribers
            if user.username not in portfolio.subscribers:
                subscribers.append(user.username)
            await get_portfolio_collection(conn).update_one(
                {"_id": portfolio.id},
                {
                    "$set": {
                        "subscribe_num": subscribe_num,
                        "subscribers": subscribers,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return ResultInResponse()


async def unsubscribe_portfolio(conn: AsyncIOMotorClient, user: User, portfolio: Portfolio):
    if portfolio.id not in user.portfolio.subscribe_info.focus_list:
        return ResultInResponse()
    user.portfolio.subscribe_info.focus_list.remove(portfolio.id)
    user.portfolio.subscribe_info.focus_num -= 1
    async with await conn.start_session() as s:
        async with s.start_transaction():
            # 更新用户subscribe_info中的订阅列表和订阅数量，同时被关注者粉丝数量-1，组合数据订阅数量-1
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"portfolio.subscribe_info": user.portfolio.subscribe_info.dict()}},
            )
            await get_user_collection(conn).update_one(
                {"username": portfolio.username},
                {"$inc": {"portfolio.subscribe_info.fans_num": -1}},
            )
            subscribe_num = portfolio.subscribe_num - 1 if portfolio.subscribe_num > 0 else 0
            subscribers = portfolio.subscribers
            if user.username in portfolio.subscribers:
                subscribers.remove(user.username)
            await get_portfolio_collection(conn).update_one(
                {"_id": portfolio.id},
                {
                    "$set": {
                        "subscribe_num": subscribe_num,
                        "subscribers": subscribers,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return ResultInResponse()


async def 创建消息(conn: AsyncIOMotorClient, user: User, usermessage: UserMessageInCreate) -> ResultInResponse:
    if usermessage.msg_type != 消息类型.notice:
        user = await get_user(conn, usermessage.username)
        if not user:
            raise NoUserError(message="消息接收人不存在！")
        result = await get_user_message_collection(conn).insert_one(usermessage.dict())
        if result.inserted_id:
            return ResultInResponse()
    else:
        users_cursor = get_user_collection(conn).find({"username": {"$ne": user.username}})
        insert_list = []
        async for user in users_cursor:
            usermessage.username = user["username"]
            insert_list.append(usermessage.dict())
        result = await get_user_message_collection(conn).insert_many(insert_list)
        if result.inserted_ids:
            return ResultInResponse()


async def 获取某用户消息列表(conn: AsyncIOMotorClient, query: dict, limit: int, skip: int, order_by: list = None) -> UserMessageListInResponse:
    message_list_cursor = get_user_message_collection(conn).find(query, limit=limit, skip=skip, sort=order_by)
    message_list = [UserMessagenInResponse(**row) async for row in message_list_cursor]
    documents_count = await get_user_message_collection(conn).count_documents(query)
    page_size = math.ceil(documents_count / limit) if limit > 0 else 1
    return UserMessageListInResponse(数据=message_list, 总数据量=documents_count, 总页数=page_size)


async def read_user_message(conn: AsyncIOMotorClient, id: Optional[str], user: User) -> ResultInResponse:
    """消息更新为已读：分为已读单条和已读所有"""
    if id:
        result = await get_user_message_collection(conn).update_one(
            {"_id": ObjectId(id)},
            {"$set": {"is_read": True, "updated_at": datetime.utcnow()}},
        )

    else:
        result = await get_user_message_collection(conn).update_many(
            {"username": user.username, "is_read": False},
            {"$set": {"is_read": True, "updated_at": datetime.utcnow()}},
        )
    if result.matched_count == result.modified_count == 1:
        return ResultInResponse()


async def update_user_roles(conn: AsyncIOMotorClient, id: Union[ObjectId, str], role: List[str]) -> ResultInResponse:
    id = id if isinstance(id, ObjectId) else ObjectId(id)
    updated_result = await get_user_collection(conn).update_one({"_id": id}, {"$set": {"roles": role}})
    if updated_result.matched_count == updated_result.modified_count == 1:
        return ResultInResponse()
