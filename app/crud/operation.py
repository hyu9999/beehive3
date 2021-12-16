from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_trend_chart_collection
from app.models.operation import TrendChart
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.operation import TrendChartInCreate, TrendChartInResponse, TrendChartInUpdate


async def create_trend_chart(conn: AsyncIOMotorClient, trend_chart: TrendChartInCreate) -> TrendChart:
    trend_chart = TrendChart(**trend_chart.dict())
    row = await get_trend_chart_collection(conn).insert_one(trend_chart.dict(exclude={"id"}))
    trend_chart.id = row.inserted_id
    return trend_chart


async def delete_trend_chart_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_trend_chart_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_trend_chart_by_id(conn: AsyncIOMotorClient, id: PyObjectId, trend_chart: TrendChartInUpdate) -> UpdateResult:
    result = await get_trend_chart_collection(conn).update_one({"_id": id}, {"$set": trend_chart.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_trend_chart_by_id(conn: AsyncIOMotorClient, id: PyObjectId, trend_chart: TrendChartInUpdate) -> UpdateResult:
    result = await get_trend_chart_collection(conn).update_one({"_id": id}, {"$set": trend_chart.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_trend_chart_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> TrendChartInResponse:
    row = await get_trend_chart_collection(conn).find_one({"_id": id})
    if row:
        return TrendChartInResponse(**row)


async def get_trend_charts(conn: AsyncIOMotorClient, query: dict) -> List[TrendChartInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_trend_chart_collection(conn).find(db_query)
    if rows:
        return [TrendChartInResponse(**row) async for row in rows]
