from typing import List

from fastapi import APIRouter, Body, Depends, Security, HTTPException, Query, Path
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.jwt import get_current_user_authorizer
from app.crud.operation import (
    create_trend_chart,
    delete_trend_chart_by_id,
    update_trend_chart_by_id,
    patch_trend_chart_by_id,
    get_trend_chart_by_id,
    get_trend_charts,
)
from app.db.mongodb import get_database
from app.enums.operation import 趋势图分类
from app.models.operation import TrendChart
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.operation import TrendChartInCreate, TrendChartInUpdate, TrendChartInResponse

router = APIRouter()


@router.post("", response_model=TrendChart, description="创建趋势图")
async def create_trend_chart_view(
    trend_chart: TrendChartInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["运营数据:创建"]),
):
    try:
        return await create_trend_chart(db, trend_chart)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建趋势图失败，错误信息: {e}")


@router.delete("/{id}", response_model=ResultInResponse, description="删除趋势图")
async def delete_trend_chart_view(
    id: PyObjectId = Path(..., description="trend_chart_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["运营数据:删除"]),
):
    try:
        return await delete_trend_chart_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除趋势图失败，错误信息: {e}")


@router.put("/{id}", response_model=UpdateResult, description="全量更新趋势图")
async def update_trend_chart_view(
    id: PyObjectId = Path(..., description="trend_chart_id"),
    trend_chart: TrendChartInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["运营数据:修改"]),
):
    try:
        return await update_trend_chart_by_id(db, id, trend_chart)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新趋势图失败，错误信息: {e}")


@router.patch("/{id}", response_model=UpdateResult, description="部分更新趋势图")
async def patch_trend_chart_view(
    id: PyObjectId = Path(..., description="trend_chart_id"),
    trend_chart: TrendChartInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["运营数据:修改"]),
):
    try:
        return await patch_trend_chart_by_id(db, id, trend_chart)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新趋势图失败，错误信息: {e}")


@router.get("/{id}", response_model=TrendChartInResponse, description="获取趋势图")
async def get_trend_chart_view(
    id: PyObjectId = Path(..., description="trend_chart_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["运营数据:查看"]),
):
    try:
        return await get_trend_chart_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取趋势图失败，错误信息: {e}")


@router.get("/list/", response_model=List[TrendChartInResponse], description="获取趋势图列表")
async def get_trend_charts_view(
    category: 趋势图分类 = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["运营数据:查看"]),
):
    try:
        db_query = {"category": category, "tdate": {"$gte": start_date, "$lte": end_date}}
        return await get_trend_charts(db, db_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取趋势图列表失败，错误信息: {e}")
