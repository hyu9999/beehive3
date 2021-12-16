from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne

from app.crud.base import get_error_log_collection, get_stock_log_collection
from app.models.log import ErrorLog, StockLog
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.log import ErrorLogInCreate, ErrorLogInResponse, ErrorLogInUpdate, StockLogInCreate, StockLogInResponse, StockLogInUpdate


async def create_error_log(conn: AsyncIOMotorClient, error_log: ErrorLogInCreate) -> ErrorLog:
    error_log = ErrorLog(**error_log.dict())
    row = await get_error_log_collection(conn).insert_one(error_log.dict(exclude={"id"}))
    error_log.id = row.inserted_id
    return error_log


async def delete_error_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_error_log_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_error_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId, error_log: ErrorLogInUpdate) -> UpdateResult:
    result = await get_error_log_collection(conn).update_one({"_id": id}, {"$set": error_log.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_error_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId, error_log: ErrorLogInUpdate) -> UpdateResult:
    result = await get_error_log_collection(conn).update_one({"_id": id}, {"$set": error_log.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_error_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ErrorLogInResponse:
    row = await get_error_log_collection(conn).find_one({"_id": id})
    if row:
        return ErrorLogInResponse(**row)


async def get_error_logs(conn: AsyncIOMotorClient, query: dict) -> List[ErrorLogInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_error_log_collection(conn).find(db_query)
    if rows:
        return [ErrorLogInResponse(**row) async for row in rows]


async def create_stock_log(conn: AsyncIOMotorClient, stock_log: StockLogInCreate) -> StockLog:
    stock_log = StockLog(**stock_log.dict())
    row = await get_stock_log_collection(conn).insert_one(stock_log.dict(exclude={"id"}))
    stock_log.id = row.inserted_id
    return stock_log


async def batch_create_stock_log(conn: AsyncIOMotorClient, stock_logs: List[StockLog]) -> ResultInResponse:
    update_list = []
    for stock_log in stock_logs:
        update_list.append(InsertOne(stock_log.dict(by_alias=True)))
    if update_list:
        await get_stock_log_collection(conn).bulk_write(update_list, ordered=False)
    return ResultInResponse()


async def delete_stock_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_stock_log_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_stock_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId, stock_log: StockLogInUpdate) -> UpdateResult:
    result = await get_stock_log_collection(conn).update_one({"_id": id}, {"$set": stock_log.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_stock_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId, stock_log: StockLogInUpdate) -> UpdateResult:
    result = await get_stock_log_collection(conn).update_one({"_id": id}, {"$set": stock_log.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_stock_log_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> StockLogInResponse:
    row = await get_stock_log_collection(conn).find_one({"_id": id})
    if row:
        return StockLogInResponse(**row)


async def get_stock_logs(conn: AsyncIOMotorClient, query: dict) -> List[StockLogInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_stock_log_collection(conn).find(db_query)
    if rows:
        return [StockLogInResponse(**row) async for row in rows]


async def get_stock_log_by_portfolio(conn: AsyncIOMotorClient, portfolio_id: PyObjectId):
    return [x async for x in get_stock_log_collection(conn).find({"portfolio": portfolio_id})]
