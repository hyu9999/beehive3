from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_activity_collection, get_activity_yield_rank_collection
from app.models.activity import Activity, ActivityYieldRank
from app.models.rwmodel import PyObjectId
from app.schema.activity import (
    ActivityInCreate,
    ActivityInResponse,
    ActivityInUpdate,
    ActivityYieldRankInCreate,
    ActivityYieldRankInResponse,
    ActivityYieldRankInUpdate,
)
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse


async def create_activity(conn: AsyncIOMotorClient, activity: ActivityInCreate) -> Activity:
    activity = Activity(**activity.dict())
    row = await get_activity_collection(conn).insert_one(activity.dict(exclude={"id"}))
    activity.id = row.inserted_id
    return activity


async def delete_activity_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_activity_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_activity_by_id(conn: AsyncIOMotorClient, id: PyObjectId, activity: ActivityInUpdate) -> UpdateResult:
    update_dict = {k: v for k, v in activity.dict().items() if v}
    if update_dict:
        result = await get_activity_collection(conn).update_one({"_id": id}, {"$set": update_dict})
        return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_activity_by_id(conn: AsyncIOMotorClient, id: PyObjectId, activity: ActivityInUpdate) -> UpdateResult:
    result = await get_activity_collection(conn).update_one({"_id": id}, {"$set": activity.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_activity_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ActivityInResponse:
    row = await get_activity_collection(conn).find_one({"_id": id})
    if row:
        return ActivityInResponse(**row)


async def get_activities(conn: AsyncIOMotorClient, query: dict) -> List[ActivityInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_activity_collection(conn).find(db_query)
    if rows:
        return [ActivityInResponse(**row) async for row in rows]


async def new_activity_yield_rank(conn: AsyncIOMotorClient, activity_yield_rank: ActivityYieldRankInCreate) -> ActivityYieldRank:
    activity_yield_rank = ActivityYieldRank(**activity_yield_rank.dict())
    row = await get_activity_yield_rank_collection(conn).insert_one(activity_yield_rank.dict(exclude={"id"}))
    activity_yield_rank.id = row.inserted_id
    return activity_yield_rank


async def delete_activity_yield_rank_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_activity_yield_rank_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_activity_yield_rank_by_id(conn: AsyncIOMotorClient, id: PyObjectId, activity_yield_rank: ActivityYieldRankInUpdate) -> UpdateResult:
    result = await get_activity_yield_rank_collection(conn).update_one({"_id": id}, {"$set": activity_yield_rank.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def patch_activity_yield_rank_by_id(conn: AsyncIOMotorClient, id: PyObjectId, activity_yield_rank: ActivityYieldRankInUpdate) -> UpdateResult:
    result = await get_activity_yield_rank_collection(conn).update_one({"_id": id}, {"$set": activity_yield_rank.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def get_activity_yield_rank_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> ActivityYieldRankInResponse:
    row = await get_activity_yield_rank_collection(conn).find_one({"_id": id})
    if row:
        return ActivityYieldRankInResponse(**row)


async def get_activity_yield_ranks(conn: AsyncIOMotorClient, query: dict) -> List[ActivityYieldRankInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_activity_yield_rank_collection(conn).find(db_query)
    if rows:
        return [ActivityYieldRankInResponse(**row) async for row in rows]
