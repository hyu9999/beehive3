from datetime import date
from typing import List, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DeleteOne, InsertOne, ReplaceOne

from app.core.errors import EntityDoesNotExist
from app.crud.base import (
    get_fund_time_series_data_collection,
    get_portfolio_assessment_time_series_data_collection,
    get_position_time_series_data_collection,
)
from app.models.rwmodel import PyObjectId
from app.models.time_series_data import (
    FundTimeSeriesDataInDB,
    PortfolioAssessmentTimeSeriesDataInDB,
    PositionTimeSeriesDataInDB,
)
from app.schema.common import ResultInResponse
from app.utils.datetime import date2datetime


async def create_position_time_series_data(
    conn: AsyncIOMotorClient, position: PositionTimeSeriesDataInDB
) -> PositionTimeSeriesDataInDB:
    """创建持仓时点数据."""
    row = await get_position_time_series_data_collection(conn).insert_one(
        position.dict(exclude={"id"})
    )
    position.id = row.inserted_id
    return position


async def bulk_write_position_time_series_data(
    conn: AsyncIOMotorClient, operations: List[Union[InsertOne, DeleteOne]]
) -> None:
    """批量写入持仓时点数据."""
    await get_position_time_series_data_collection(conn).bulk_write(operations)


async def delete_position_time_series_data_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
) -> ResultInResponse:
    """删除持仓时点数据."""
    result = await get_position_time_series_data_collection(conn).delete_one(
        {"_id": _id}
    )
    if result.deleted_count == 0:
        raise EntityDoesNotExist
    return ResultInResponse()


async def get_position_time_series_data(
    conn: AsyncIOMotorClient,
    *,
    fund_id: Optional[str] = None,
    tdate: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[PositionTimeSeriesDataInDB]:
    """查询持仓时点数据."""
    if (tdate and start_date) or (tdate and end_date):
        raise ValueError("不可以同时指定`tdate`和 `start_date`或`end_date` .")
    query = {}
    if fund_id is not None:
        query["fund_id"] = fund_id
    if tdate is not None:
        query["tdate"] = date2datetime(tdate)
    if end_date is not None:
        query["tdate"] = {"$lte": date2datetime(end_date, "max")}
    if start_date is not None:
        query["tdate"] = {"$gte": date2datetime(start_date)}
    if start_date is not None and end_date is not None:
        query["tdate"] = {
            "$gte": date2datetime(start_date),
            "$lte": date2datetime(end_date, "max"),
        }
    cursor = get_position_time_series_data_collection(conn).find(query).sort("tdate")
    return [PositionTimeSeriesDataInDB(**flow) async for flow in cursor]


async def create_fund_time_series_data(
    conn: AsyncIOMotorClient, fund: FundTimeSeriesDataInDB
) -> FundTimeSeriesDataInDB:
    """创建资产时点数据."""
    row = await get_fund_time_series_data_collection(conn).insert_one(
        fund.dict(exclude={"id"})
    )
    fund.id = row.inserted_id
    return fund


async def bulk_write_fund_time_series_data(
    conn: AsyncIOMotorClient, operations: List[Union[InsertOne, DeleteOne, ReplaceOne]]
) -> None:
    """批量写入资产时点数据."""
    await get_fund_time_series_data_collection(conn).bulk_write(operations)


async def delete_fund_time_series_data_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
) -> ResultInResponse:
    """删除资产时点数据."""
    result = await get_fund_time_series_data_collection(conn).delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise EntityDoesNotExist
    return ResultInResponse()


async def get_fund_time_series_data(
    conn: AsyncIOMotorClient,
    *,
    fund_id: Optional[str] = None,
    tdate: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[FundTimeSeriesDataInDB]:
    """查询资产时点数据."""
    query = {}
    if (tdate and start_date) or (tdate and end_date):
        raise ValueError("不可以同时指定`tdate`和 `start_date`或`end_date` .")
    if fund_id is not None:
        query["fund_id"] = fund_id
    if tdate is not None:
        query["tdate"] = date2datetime(tdate)
    if end_date is not None:
        query["tdate"] = {"$lte": date2datetime(end_date, "max")}
    if start_date is not None and end_date is not None:
        query["tdate"] = {
            "$gte": date2datetime(start_date),
            "$lte": date2datetime(end_date, "max"),
        }
    cursor = get_fund_time_series_data_collection(conn).find(query).sort("tdate")
    return [FundTimeSeriesDataInDB(**flow) async for flow in cursor]


async def create_portfolio_assessment_time_series_data(
    conn: AsyncIOMotorClient, assessment: PortfolioAssessmentTimeSeriesDataInDB
) -> PortfolioAssessmentTimeSeriesDataInDB:
    """创建组合评估时点数据."""
    row = await get_portfolio_assessment_time_series_data_collection(conn).insert_one(
        assessment.dict(exclude={"id"})
    )
    assessment.id = row.inserted_id
    return assessment


async def bulk_write_portfolio_assessment_time_series_data(
    conn: AsyncIOMotorClient, operations: List[Union[InsertOne, DeleteOne, ReplaceOne]]
) -> None:
    """批量写入组合评估数据."""
    await get_portfolio_assessment_time_series_data_collection(conn).bulk_write(
        operations
    )


async def get_portfolio_assessment_time_series_data(
    conn: AsyncIOMotorClient,
    *,
    portfolio: Optional[PyObjectId] = None,
    tdate: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[PortfolioAssessmentTimeSeriesDataInDB]:
    """查询组合评估时点数据."""
    query = {}
    if (tdate and start_date) or (tdate and end_date):
        raise ValueError("不可以同时指定`tdate`和 `start_date`或`end_date` .")
    if portfolio is not None:
        query["portfolio"] = portfolio
    if tdate is not None:
        query["tdate"] = date2datetime(tdate)
    if end_date is not None:
        query["tdate"] = {"$lte": date2datetime(end_date, "max")}
    if start_date is not None and end_date is not None:
        query["tdate"] = {
            "$gte": date2datetime(start_date),
            "$lte": date2datetime(end_date, "max"),
        }
    cursor = (
        get_portfolio_assessment_time_series_data_collection(conn)
        .find(query)
        .sort("tdate")
    )
    return [PortfolioAssessmentTimeSeriesDataInDB(**flow) async for flow in cursor]
