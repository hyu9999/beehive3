from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends, Security, Query, Path
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.jwt import get_current_user_authorizer
from app.crud.activity import (
    create_activity,
    delete_activity_by_id,
    update_activity_by_id,
    patch_activity_by_id,
    get_activity_by_id,
    get_activities,
    new_activity_yield_rank,
    delete_activity_yield_rank_by_id,
    update_activity_yield_rank_by_id,
    patch_activity_yield_rank_by_id,
    get_activity_yield_rank_by_id,
    get_activity_yield_ranks,
)
from app.db.mongodb import get_database
from app.enums.activity import 活动状态
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

router = APIRouter()


@router.post("", response_model=Activity, description="创建活动")
async def create_view(
    activity: ActivityInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:创建"]),
):
    return await create_activity(db, activity)


@router.get("/list", response_model=List[ActivityInResponse], description="获取活动列表")
async def list_view(
    name: List[str] = Query(None, description="活动名称"),
    status: 活动状态 = Query(None, description="活动状态"),
    start_time: datetime = Query(None, description="活动结束时间"),
    end_time: datetime = Query(None, description="活动开始时间"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:查看"]),
):
    db_query = {"status": status}
    if name:
        db_query["name"] = {"$in": name}
    if start_time:
        db_query["start_time"] = {"$gte": start_time}
    if end_time:
        db_query["end_time"] = {"$lte": end_time}
    return await get_activities(db, db_query)


@router.post("/yield_rank", response_model=ActivityYieldRank, description="创建活动收益排行")
async def create_activity_yield_rank_view(
    activity_yield_rank: ActivityYieldRankInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:创建"]),
):
    return await new_activity_yield_rank(db, activity_yield_rank)


@router.delete("/{id}", response_model=ResultInResponse, description="删除活动")
async def delete_view(
    id: PyObjectId = Path(..., description="activity_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:删除"]),
):
    return await delete_activity_by_id(db, id)


@router.put("/{id}", response_model=UpdateResult, description="全量更新活动")
async def put_view(
    id: PyObjectId = Path(..., description="activity_id"),
    activity: ActivityInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:修改"]),
):
    return await update_activity_by_id(db, id, activity)


@router.patch("/{id}", response_model=UpdateResult, description="部分更新活动")
async def patch_view(
    id: PyObjectId = Path(..., description="activity_id"),
    activity: ActivityInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:修改"]),
):
    return await patch_activity_by_id(db, id, activity)


@router.get("/{id}", response_model=ActivityInResponse, description="获取活动")
async def get_view(
    id: PyObjectId = Path(..., description="activity_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:查看"]),
):
    return await get_activity_by_id(db, id)


@router.get("/yield_rank/list", response_model=List[ActivityYieldRankInResponse], description="获取活动收益排行列表")
async def activity_yield_ranks_list_view(
    portfolio: List[PyObjectId] = Query(None, description="组合id"),
    activity: List[PyObjectId] = Query(None, description="活动id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:查看"]),
):
    db_query = {}
    if activity:
        db_query["activity"] = {"$in": activity}
    if portfolio:
        db_query["portfolio"] = {"$in": portfolio}
    return await get_activity_yield_ranks(db, db_query)


@router.delete("/yield_rank/{id}", response_model=ResultInResponse, description="删除活动收益排行")
async def activity_yield_rank_delete_view(
    id: PyObjectId = Path(..., description="activity_yield_rank_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:删除"]),
):
    return await delete_activity_yield_rank_by_id(db, id)


@router.put("/yield_rank/{id}", response_model=UpdateResult, description="全量更新活动收益排行")
async def activity_yield_rank_put_view(
    id: PyObjectId = Path(..., description="activity_yield_rank_id"),
    activity_yield_rank: ActivityYieldRankInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:修改"]),
):
    return await update_activity_yield_rank_by_id(db, id, activity_yield_rank)


@router.patch("/yield_rank/{id}", response_model=UpdateResult, description="部分更新活动收益排行")
async def activity_yield_rank_patch_view(
    id: PyObjectId = Path(..., description="activity_yield_rank_id"),
    activity_yield_rank: ActivityYieldRankInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:修改"]),
):
    return await patch_activity_yield_rank_by_id(db, id, activity_yield_rank)


@router.get("/yield_rank/{id}", response_model=ActivityYieldRankInResponse, description="获取活动收益排行")
async def activity_yield_rank_get_view(
    id: PyObjectId = Path(..., description="activity_yield_rank_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["活动:查看"]),
):
    return await get_activity_yield_rank_by_id(db, id)
