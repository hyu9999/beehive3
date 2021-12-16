from datetime import datetime
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.errors import EntityDoesNotExist
from app.enums.zvt_data import ZvtDataLogState
from app.models.base.zvt_data_log import ZvtDataLogType
from app.models.rwmodel import PyObjectId
from app.models.zvt_data_log import ZvtDataLogInDB, ZvtDataLogTypeInDB
from app.crud.base import get_zvt_data_log_collection, get_zvt_data_log_type_collection
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.zvt_data_log import ZvtDataLogInUpdate


async def create_zvt_data_log(
    conn: AsyncIOMotorClient,
    zvt_data_log_in_db: ZvtDataLogInDB
) -> ZvtDataLogInDB:
    result = await get_zvt_data_log_collection(conn).insert_one(zvt_data_log_in_db.dict(exclude={"id"}))
    zvt_data_log_in_db.id = result.inserted_id
    return zvt_data_log_in_db


async def create_zvt_data_log_type(
    conn: AsyncIOMotorClient,
    zvt_data_log_type_in_db: ZvtDataLogTypeInDB
) -> ZvtDataLogTypeInDB:
    result = await get_zvt_data_log_type_collection(conn).insert_one(zvt_data_log_type_in_db.dict(exclude={"id"}))
    zvt_data_log_type_in_db.id = result.inserted_id
    return zvt_data_log_type_in_db


async def get_zvt_data_type_by_name(
    conn: AsyncIOMotorClient,
    name: str,
) -> ZvtDataLogTypeInDB:
    row = await get_zvt_data_log_type_collection(conn).find_one({"name": name})
    if row:
        return ZvtDataLogTypeInDB(**row)
    raise EntityDoesNotExist


async def get_zvt_data_type_list(
    conn: AsyncIOMotorClient,
    limit: int,
    skip: int,
) -> List[ZvtDataLogTypeInDB]:
    cursor = get_zvt_data_log_type_collection(conn).find()
    return [ZvtDataLogTypeInDB(**obj) async for obj in cursor.skip(skip).limit(limit)]


async def update_zvt_data_type_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
    data_type: ZvtDataLogType
) -> UpdateResult:
    result = await get_zvt_data_log_collection(conn).update_one({"_id": _id}, {"$set": data_type.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_zvt_data_logs(
    conn: AsyncIOMotorClient,
    *,
    limit: int,
    skip: int,
    data_type: Optional[ZvtDataLogType] = None
) -> List[ZvtDataLogInDB]:
    query = {}
    if data_type is not None:
        query["data_type"] = data_type
    cursor = get_zvt_data_log_collection(conn).find(query)
    return [ZvtDataLogInDB(**obj) async for obj in cursor.skip(skip).limit(limit)]


async def get_zvt_data_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId
) -> ZvtDataLogInDB:
    row = await get_zvt_data_log_collection(conn).find_one({"_id": _id})
    if row:
        return ZvtDataLogInDB(**row)
    raise EntityDoesNotExist


async def update_zvt_data_log_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
    zvt_data_in_update: ZvtDataLogInUpdate
) -> UpdateResult:
    result = await get_zvt_data_log_collection(conn).update_one({"_id": _id}, {"$set": zvt_data_in_update.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def delete_zvt_data_log_type_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
) -> ResultInResponse:
    result = await get_zvt_data_log_type_collection(conn).delete_one({"_id": _id})
    if result.deleted_count > 0:
        return ResultInResponse()
    raise EntityDoesNotExist


async def partial_update_zvt_data_log_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
    *,
    data_type: Optional[ZvtDataLogType] = None,
    name: Optional[str] = None,
    data_class: Optional[str] = None,
    desc: Optional[str] = None,
    update_time: Optional[str] = None,
    state: Optional[ZvtDataLogState] = None
) -> UpdateResult:
    query = {}
    if data_type is not None:
        query["data_type"] = data_type
    if name is not None:
        query["name"] = name
    if data_class is not None:
        query["data_class"] = data_class
    if desc is not None:
        query["desc"] = desc
    if update_time is not None:
        query["update_time"] = update_time
    if state is not None:
        query["state"] = state
        query["updated_at"] = datetime.utcnow()
    result = await get_zvt_data_log_collection(conn).update_one({"_id": _id}, {"$set": query})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def delete_zvt_data_log_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
) -> ResultInResponse:
    result = await get_zvt_data_log_collection(conn).delete_one({"_id": _id})
    if result.deleted_count > 0:
        return ResultInResponse()
    raise EntityDoesNotExist
