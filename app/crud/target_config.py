from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_trade_stats_conf_collection, get_stock_stats_conf_collection, \
    get_portfolio_target_conf_collection
from app.models.rwmodel import PyObjectId
from app.models.target_config import TradeStatsConf, StockStatsConf, PortfolioTargetConf
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.target_config import (
    TradeStatsConfInCreate,
    TradeStatsConfInResponse,
    TradeStatsConfInUpdate,
    StockStatsConfInCreate,
    StockStatsConfInResponse,
    StockStatsConfInUpdate,
    PortfolioTargetConfInCreate,
    PortfolioTargetConfInResponse,
    PortfolioTargetConfInUpdate,
)


async def create_trade_stats_conf(conn: AsyncIOMotorClient, trade_stats_conf: TradeStatsConfInCreate) -> TradeStatsConf:
    trade_stats_conf = TradeStatsConf(**trade_stats_conf.dict())
    row = await get_trade_stats_conf_collection(conn).insert_one(trade_stats_conf.dict(exclude={"id"}))
    trade_stats_conf.id = row.inserted_id
    return trade_stats_conf


async def delete_trade_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_trade_stats_conf_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_trade_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId, trade_stats_conf: TradeStatsConfInUpdate) -> UpdateResult:
    result = await get_trade_stats_conf_collection(conn).update_one({"_id": id}, {"$set": trade_stats_conf.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_trade_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId, trade_stats_conf: TradeStatsConfInUpdate) -> UpdateResult:
    result = await get_trade_stats_conf_collection(conn).update_one({"_id": id}, {"$set": trade_stats_conf.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_trade_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> TradeStatsConfInResponse:
    row = await get_trade_stats_conf_collection(conn).find_one({"_id": id})
    if row:
        return TradeStatsConfInResponse(**row)


async def get_trade_stats_confs(conn: AsyncIOMotorClient, query: dict) -> List[TradeStatsConfInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_trade_stats_conf_collection(conn).find(db_query)
    if rows:
        return [TradeStatsConfInResponse(**row) async for row in rows]


async def create_stock_stats_conf(conn: AsyncIOMotorClient, stock_stats_conf: StockStatsConfInCreate) -> StockStatsConf:
    stock_stats_conf = StockStatsConf(**stock_stats_conf.dict())
    row = await get_stock_stats_conf_collection(conn).insert_one(stock_stats_conf.dict(exclude={"id"}))
    stock_stats_conf.id = row.inserted_id
    return stock_stats_conf


async def delete_stock_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_stock_stats_conf_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_stock_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId, stock_stats_conf: StockStatsConfInUpdate) -> UpdateResult:
    result = await get_stock_stats_conf_collection(conn).update_one({"_id": id}, {"$set": stock_stats_conf.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_stock_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId, stock_stats_conf: StockStatsConfInUpdate) -> UpdateResult:
    result = await get_stock_stats_conf_collection(conn).update_one({"_id": id}, {"$set": stock_stats_conf.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_stock_stats_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> StockStatsConfInResponse:
    row = await get_stock_stats_conf_collection(conn).find_one({"_id": id})
    if row:
        return StockStatsConfInResponse(**row)


async def get_stock_stats_confs(conn: AsyncIOMotorClient, query: dict) -> List[StockStatsConfInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_stock_stats_conf_collection(conn).find(db_query)
    if rows:
        return [StockStatsConfInResponse(**row) async for row in rows]


async def create_portfolio_target_conf(conn: AsyncIOMotorClient, portfolio_target_conf: PortfolioTargetConfInCreate) -> PortfolioTargetConf:
    portfolio_target_conf = PortfolioTargetConf(**portfolio_target_conf.dict())
    row = await get_portfolio_target_conf_collection(conn).insert_one(portfolio_target_conf.dict(exclude={"id"}))
    portfolio_target_conf.id = row.inserted_id
    return portfolio_target_conf


async def delete_portfolio_target_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_portfolio_target_conf_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_portfolio_target_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId, portfolio_target_conf: PortfolioTargetConfInUpdate) -> UpdateResult:
    result = await get_portfolio_target_conf_collection(conn).update_one({"_id": id}, {"$set": portfolio_target_conf.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_portfolio_target_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId, portfolio_target_conf: PortfolioTargetConfInUpdate) -> UpdateResult:
    result = await get_portfolio_target_conf_collection(conn).update_one({"_id": id}, {"$set": portfolio_target_conf.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_portfolio_target_conf_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> PortfolioTargetConfInResponse:
    row = await get_portfolio_target_conf_collection(conn).find_one({"_id": id})
    if row:
        return PortfolioTargetConfInResponse(**row)


async def get_portfolio_target_confs(conn: AsyncIOMotorClient, query: dict) -> List[PortfolioTargetConfInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_portfolio_target_conf_collection(conn).find(db_query)
    if rows:
        return [PortfolioTargetConfInResponse(**row) async for row in rows]
