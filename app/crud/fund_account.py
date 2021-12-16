from datetime import date
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

from app.core.errors import EntityDoesNotExist
from app.crud.base import (
    get_fund_account_collection,
    get_fund_account_flow_collection,
    get_fund_account_position_collection,
)
from app.enums.fund_account import Exchange, FlowTType
from app.models.fund_account import (
    FundAccountFlowInDB,
    FundAccountInDB,
    FundAccountPositionInDB,
)
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.fund_account import FundAccountInUpdate, FundAccountPositionInUpdate
from app.utils.datetime import date2datetime


async def create_fund_account(
    conn: AsyncIOMotorClient, fund_account: FundAccountInDB
) -> FundAccountInDB:
    """创建资金账户."""
    row = await get_fund_account_collection(conn).insert_one(
        fund_account.dict(exclude={"id"})
    )
    fund_account.id = row.inserted_id
    return fund_account


async def bulk_write_fund_account(
    conn: AsyncIOMotorClient, operations: List[UpdateOne]
) -> None:
    """批量写入资金账户数据."""
    await get_fund_account_collection(conn).bulk_write(operations)


async def get_fund_account_by_id(
    conn: AsyncIOMotorClient, _id: PyObjectId
) -> FundAccountInDB:
    """获取资金账户."""
    row = await get_fund_account_collection(conn).find_one({"_id": _id})
    if row:
        return FundAccountInDB(**row)
    raise EntityDoesNotExist


async def update_fund_account_by_id(
    conn: AsyncIOMotorClient, _id: PyObjectId, fund_account: FundAccountInUpdate
) -> UpdateResult:
    """更新资金账户."""
    result = await get_fund_account_collection(conn).update_one(
        {"_id": _id}, {"$set": fund_account.dict()}
    )
    return UpdateResult(
        matched_count=result.matched_count, modified_count=result.modified_count
    )


async def delete_fund_account(
    conn: AsyncIOMotorClient, _id: PyObjectId
) -> ResultInResponse:
    """删除资金账户."""
    result = await get_fund_account_collection(conn).delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise EntityDoesNotExist
    return ResultInResponse()


async def create_fund_account_flow(
    conn: AsyncIOMotorClient, fund_account_flow: FundAccountFlowInDB
) -> FundAccountFlowInDB:
    """创建资金账户流水."""
    row = await get_fund_account_flow_collection(conn).insert_one(
        fund_account_flow.dict(exclude={"id"})
    )
    fund_account_flow.id = row.inserted_id
    return fund_account_flow


async def get_fund_account_flow_by_id(
    conn: AsyncIOMotorClient, _id: PyObjectId
) -> FundAccountFlowInDB:
    """获取资金流水."""
    row = await get_fund_account_flow_collection(conn).find_one({"_id": _id})
    if row:
        return FundAccountFlowInDB(**row)
    raise EntityDoesNotExist


async def get_fund_account_flow_from_db(
    conn: AsyncIOMotorClient,
    *,
    fund_id: Optional[str] = None,
    ttype: Optional[List[FlowTType]] = None,
    start_date: Optional[date] = None,
    tdate: Optional[date] = None,
    end_date: Optional[date] = None,
    symbol: Optional[str] = None,
) -> List[FundAccountFlowInDB]:
    """查询资金账户流水."""
    query = {}
    if fund_id is not None:
        query["fund_id"] = fund_id
    if ttype is not None:
        query["ttype"] = {"$in": [t.value for t in ttype]}
    if start_date is not None:
        query["tdate"] = {"$gte": date2datetime(start_date)}
    if end_date is not None:
        query["tdate"] = {"$lte": date2datetime(end_date, "max")}
    if start_date is not None and end_date is not None:
        query["tdate"] = {
            "$gte": date2datetime(start_date),
            "$lte": date2datetime(end_date, "max"),
        }
    if symbol is not None:
        query["symbol"] = symbol
    if tdate is not None:
        query["tdate"] = date2datetime(tdate)
    cursor = get_fund_account_flow_collection(conn).find(query).sort("tdate")
    return [FundAccountFlowInDB(**flow) async for flow in cursor]


async def update_fund_account_flow_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
    fund_account_flow: FundAccountFlowInDB,
) -> UpdateResult:
    """更新资金账户流水."""
    result = await get_fund_account_flow_collection(conn).update_one(
        {"_id": _id}, {"$set": fund_account_flow.dict(exclude={"id"})}
    )
    return UpdateResult(
        matched_count=result.matched_count, modified_count=result.modified_count
    )


async def delete_fund_account_flow_by_id(
    conn: AsyncIOMotorClient, _id: PyObjectId
) -> ResultInResponse:
    """删除资金账户流水."""
    result = await get_fund_account_flow_collection(conn).delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise EntityDoesNotExist
    return ResultInResponse()


async def delete_fund_account_flow_many(
    conn: AsyncIOMotorClient, query: dict
) -> ResultInResponse:
    """删除资金账户流水."""
    await get_fund_account_flow_collection(conn).delete_many(query)
    return ResultInResponse()


async def create_fund_account_position(
    conn: AsyncIOMotorClient, position: FundAccountPositionInDB
) -> FundAccountPositionInDB:
    """创建资金账户持仓."""
    row = await get_fund_account_position_collection(conn).insert_one(
        position.dict(exclude={"id"})
    )
    position.id = row.inserted_id
    return position


async def delete_fund_account_position_by_id(
    conn: AsyncIOMotorClient, position_id: PyObjectId
) -> ResultInResponse:
    """删除资金账户持仓."""
    result = await get_fund_account_position_collection(conn).delete_one(
        {"_id": position_id}
    )
    if result.deleted_count == 0:
        raise EntityDoesNotExist
    return ResultInResponse()


async def update_fund_account_position_by_id(
    conn: AsyncIOMotorClient,
    position_id: PyObjectId,
    position: FundAccountPositionInUpdate,
) -> UpdateResult:
    """更新资金账户持仓."""
    result = await get_fund_account_position_collection(conn).update_one(
        {"_id": position_id}, {"$set": position.dict()}
    )
    return UpdateResult(
        matched_count=result.matched_count, modified_count=result.modified_count
    )


async def get_fund_account_position_from_db(
    conn: AsyncIOMotorClient,
    *,
    fund_id: Optional[str] = None,
    symbol: Optional[str] = None,
    exchange: Optional[Exchange] = None,
) -> List[FundAccountPositionInDB]:
    """查找资金账户持仓."""
    query = {}
    if fund_id is not None:
        query["fund_id"] = fund_id
    if symbol is not None:
        query["symbol"] = symbol
    if exchange is not None:
        query["exchange"] = exchange
    cursor = get_fund_account_position_collection(conn).find(query)
    return [FundAccountPositionInDB(**position) async for position in cursor]


async def get_fund_account_position_by_id(
    conn: AsyncIOMotorClient, position_id: PyObjectId
) -> FundAccountPositionInDB:
    row = await get_fund_account_position_collection(conn).find_one(
        {"_id": position_id}
    )
    if row:
        return FundAccountPositionInDB(**row)
    raise EntityDoesNotExist
