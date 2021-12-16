from typing import List, Dict, Union

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_favorite_stock_collection, get_stock_pool_collection, get_stock_collection
from app.models.rwmodel import PyObjectId
from app.models.stock import FavoriteStock, StockPool
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.stock import FavoriteStockInCreate, FavoriteStockInResponse, FavoriteStockInUpdate, StockPoolInCreate, \
    StockPoolInUpdate, StockPoolInResponse, 股票InResponse


async def create_favorite_stock(conn: AsyncIOMotorClient, stock: FavoriteStockInCreate) -> FavoriteStock:
    stock = FavoriteStock(**stock.dict())
    row = await get_favorite_stock_collection(conn).insert_one(stock.dict(exclude={"id"}))
    stock.id = row.inserted_id
    return stock


async def delete_favorite_stock_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_favorite_stock_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def delete_favorite_stock_by_unique(conn: AsyncIOMotorClient, filter: dict, update: dict) -> UpdateResult:
    """根据联合主键，移除stocks列表中的指定数据"""
    result = await get_favorite_stock_collection(conn).update_one(filter, {"$pull": {"stocks": update}})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def update_favorite_stock_by_id(conn: AsyncIOMotorClient, id: PyObjectId, stock: FavoriteStockInUpdate) -> UpdateResult:
    result = await get_favorite_stock_collection(conn).update_one({"_id": id}, {"$set": stock.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_favorite_stock_by_id(conn: AsyncIOMotorClient, id: PyObjectId, stock: FavoriteStockInUpdate) -> UpdateResult:
    result = await get_favorite_stock_collection(conn).update_one({"_id": id}, {"$set": stock.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_favorite_stock_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> FavoriteStockInResponse:
    row = await get_favorite_stock_collection(conn).find_one({"_id": id})
    if row:
        return FavoriteStockInResponse(**row)


async def get_favorite_stock_by_unique(conn: AsyncIOMotorClient, query: dict) -> FavoriteStockInResponse:
    """根据联合主键获取单条数据"""
    row = await get_favorite_stock_collection(conn).find_one(query)
    if row:
        return FavoriteStockInResponse(**row)


async def get_favorite_stocks(conn: AsyncIOMotorClient, query: dict) -> List[FavoriteStockInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_favorite_stock_collection(conn).find(db_query)
    if rows:
        return [FavoriteStockInResponse(**row) async for row in rows]


# 股票池
async def get_stock_pool_by_unique(conn: AsyncIOMotorClient, query: dict) -> StockPool:
    row = await get_stock_pool_collection(conn).find_one(query)
    if row:
        return StockPoolInResponse(**row)


async def get_stock_pool_list(conn: AsyncIOMotorClient, query: dict) -> List[StockPoolInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_stock_pool_collection(conn).find(db_query)
    if rows:
        return [StockPoolInResponse(**row) async for row in rows]


async def create_stock_pool(conn: AsyncIOMotorClient, stocks: List[StockPoolInCreate]) -> ResultInResponse:
    result = await get_stock_pool_collection(conn).insert_many([x.dict(exclude={"id"}) for x in stocks])
    if result.inserted_ids:
        return ResultInResponse()


async def batch_create_stock_pool(conn: AsyncIOMotorClient, stock_list: List[StockPoolInCreate]) -> StockPool:
    result = await get_stock_pool_collection(conn).insert_many([x.dict(exclude={"id"}) for x in stock_list])
    return result.inserted_ids


async def batch_delete_stock_pool(conn: AsyncIOMotorClient, filters: dict) -> StockPool:
    result = await get_stock_pool_collection(conn).delete_many(filters)
    return result.inserted_ids


async def delete_stock_pool_by_unique(conn: AsyncIOMotorClient, query: dict, many: bool = False) -> ResultInResponse:
    query = {k: v for k, v in query.items() if v}
    if many:
        result = await get_stock_pool_collection(conn).delete_many(query)
    else:
        result = await get_stock_pool_collection(conn).delete_one(query)
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_stock_pool_by_unique(conn: AsyncIOMotorClient, query: dict, stock: StockPoolInUpdate) -> UpdateResult:
    result = await get_favorite_stock_collection(conn).update_one(query, {"$set": stock.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def batch_update_stock_pool(conn: AsyncIOMotorClient, query: dict, stock: StockPoolInUpdate) -> UpdateResult:
    result = await get_favorite_stock_collection(conn).update_many(query, {"$set": stock.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def bulk_write_stock_pool(conn: AsyncIOMotorClient, data: List[object]):
    result = await get_stock_pool_collection(conn).bulk_write(data)
    return result


async def 查询股票列表(conn: AsyncIOMotorClient, filters: dict = None, limit: int = 10, skip: int = 0) -> List[股票InResponse]:
    filters = filters or {}
    db_query = {key: value for key, value in filters.items() if value}
    list_cursor = get_stock_collection(conn).find(db_query, limit=limit, skip=skip)
    response = [股票InResponse(**row) async for row in list_cursor]
    return response


async def bulk_write_stock(conn: AsyncIOMotorClient, data: List[object]):
    result = await get_stock_collection(conn).bulk_write(data)
    return result
