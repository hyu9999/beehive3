from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Security
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.background import BackgroundTasks

from app.core.errors import NoPortfolioError, PortfolioSyncTypeError
from app.core.jwt import get_current_user_authorizer
from app.crud.log import (
    create_error_log,
    delete_error_log_by_id,
    get_error_log_by_id,
    get_error_logs,
    patch_error_log_by_id,
    update_error_log_by_id,
)
from app.db.mongodb import get_database
from app.enums.log import 日志分类
from app.models.log import ErrorLog
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.log import ErrorLogInCreate, ErrorLogInResponse, ErrorLogInUpdate

router = APIRouter()


@router.post("/error", response_model=ErrorLog, description="创建ErrorLog")
async def create_error_log_view(
    error_log: ErrorLogInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["日志:创建"]),
):
    try:
        return await create_error_log(db, error_log)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建ErrorLog失败，错误信息: {e}")


@router.delete("/error/{id}", response_model=ResultInResponse, description="删除ErrorLog")
async def delete_error_log_view(
    id: PyObjectId = Path(..., description="error_log_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["日志:删除"]),
):
    try:
        return await delete_error_log_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除ErrorLog失败，错误信息: {e}")


@router.put("/error/{id}", response_model=UpdateResult, description="全量更新ErrorLog")
async def update_error_log_view(
    id: PyObjectId = Path(..., description="error_log_id"),
    error_log: ErrorLogInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["日志:修改"]),
):
    try:
        return await update_error_log_by_id(db, id, error_log)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新ErrorLog失败，错误信息: {e}")


@router.patch("/error/{id}", response_model=UpdateResult, description="部分更新ErrorLog")
async def patch_error_log_view(
    id: PyObjectId = Path(..., description="error_log_id"),
    error_log: ErrorLogInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["日志:修改"]),
):
    try:
        return await patch_error_log_by_id(db, id, error_log)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新ErrorLog失败，错误信息: {e}")


@router.get("/error/{id}", response_model=ErrorLogInResponse, description="获取ErrorLog")
async def get_error_log_view(
    id: PyObjectId = Path(..., description="error_log_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["日志:查看"]),
):
    try:
        return await get_error_log_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取ErrorLog失败，错误信息: {e}")


@router.get(
    "/error/list", response_model=List[ErrorLogInResponse], description="获取ErrorLog列表"
)
async def get_error_logs_view(
    category: 日志分类 = Query(None),
    status: str = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["日志:查看"]),
):
    try:
        db_query = {"category": category, "status": status}
        return await get_error_logs(db, db_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取ErrorLog列表失败，错误信息: {e}")
