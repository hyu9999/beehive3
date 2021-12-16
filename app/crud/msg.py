from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_msg_config_collection
from app.models.msg import MessageConfig
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.msg import MessageConfigInCreate, MessageConfigInResponse, MessageConfigInUpdate


async def create_msg_config(conn: AsyncIOMotorClient, msg_config: MessageConfigInCreate) -> MessageConfig:
    msg_config = MessageConfig(**msg_config.dict())
    row = await get_msg_config_collection(conn).insert_one(msg_config.dict(exclude={"id"}))
    msg_config.id = row.inserted_id
    return msg_config


async def delete_msg_config_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_msg_config_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_msg_config_by_id(conn: AsyncIOMotorClient, id: PyObjectId, msg_config: MessageConfigInUpdate) -> UpdateResult:
    result = await get_msg_config_collection(conn).update_one({"_id": id}, {"$set": msg_config.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_msg_config_by_id(conn: AsyncIOMotorClient, id: PyObjectId, msg_config: MessageConfigInUpdate) -> UpdateResult:
    result = await get_msg_config_collection(conn).update_one({"_id": id}, {"$set": msg_config.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_msg_config_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> MessageConfigInResponse:
    row = await get_msg_config_collection(conn).find_one({"_id": id})
    if row:
        return MessageConfigInResponse(**row)


async def get_msg_configs(conn: AsyncIOMotorClient, query: dict) -> List[MessageConfigInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_msg_config_collection(conn).find(db_query)
    if rows:
        return [MessageConfigInResponse(**row) async for row in rows]
