from typing import List, Optional

from fastapi import APIRouter, Depends, Body, Path, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.errors import EntityDoesNotExist
from app.crud.zvt_data_log import create_zvt_data_log, get_zvt_data_logs, get_zvt_data_by_id, \
    partial_update_zvt_data_log_by_id, delete_zvt_data_log_by_id, create_zvt_data_log_type, get_zvt_data_type_by_name, \
    get_zvt_data_type_list, update_zvt_data_type_by_id, delete_zvt_data_log_type_by_id
from app.db.mongodb import get_database
from app.models.base.zvt_data_log import ZvtDataLogType
from app.models.rwmodel import PyObjectId
from app.models.zvt_data_log import ZvtDataLogInDB, ZvtDataLogTypeInDB
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.zvt_data_log import ZvtDataLogInCreate, ZvtDataLogInPartialUpdate

router = APIRouter()


@router.post("/", response_model=ZvtDataLogInDB, description="创建ZVT数据日志")
async def create_zvt_data_log_view(
    db: AsyncIOMotorClient = Depends(get_database),
    zvt_data_in_create: ZvtDataLogInCreate = Body(...)
):
    try:
        await get_zvt_data_type_by_name(db, zvt_data_in_create.data_type)
    except EntityDoesNotExist:
        raise HTTPException(status_code=400, detail="该名称的数据类型不存在.")
    else:
        return await create_zvt_data_log(db, ZvtDataLogInDB(**zvt_data_in_create.dict()))


@router.post("/data_type/", response_model=ZvtDataLogTypeInDB, description="创建ZVT数据日志数据类型")
async def create_zvt_data_log_type_view(
    db: AsyncIOMotorClient = Depends(get_database),
    zvt_data_type: ZvtDataLogType = Body(...)
):
    try:
        await get_zvt_data_type_by_name(db, zvt_data_type.name)
    except EntityDoesNotExist:
        return await create_zvt_data_log_type(db, ZvtDataLogTypeInDB(**zvt_data_type.dict()))
    else:
        raise HTTPException(status_code=400, detail="该名称的数据类型已存在.")


@router.get("/data_type/", response_model=List[ZvtDataLogTypeInDB], description="获取ZVT数据日志数据类型列表")
async def get_zvt_data_log_type_list_view(
    db: AsyncIOMotorClient = Depends(get_database),
    limit: int = Query(20, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
):
    return await get_zvt_data_type_list(db, limit, skip)


@router.put("/data_type/{_id}", response_model=UpdateResult, description="更新ZVT数据日志数据类型")
async def update_zvt_data_log_type_view(
    db: AsyncIOMotorClient = Depends(get_database),
    _id: PyObjectId = Path(...),
    data_type: ZvtDataLogType = Body(...),
):
    try:
        await get_zvt_data_type_by_name(db, data_type.name)
    except EntityDoesNotExist:
        return await update_zvt_data_type_by_id(db, _id, data_type)
    else:
        raise HTTPException(status_code=400, detail="该名称的数据类型已存在.")


@router.delete("/data_type/{_id}", response_model=ResultInResponse, description="删除ZVT数据日志数据类型")
async def delete_zvt_data_log_type_view(
    db: AsyncIOMotorClient = Depends(get_database),
    _id: PyObjectId = Path(...),
):
    try:
        return await delete_zvt_data_log_type_by_id(db, _id)
    except EntityDoesNotExist:
        return HTTPException(status_code=404, detail="未找要删除的数据.")


@router.get("/", response_model=List[ZvtDataLogInDB], description="查询ZVT数据日志列表")
async def list_zvt_data_log_view(
    db: AsyncIOMotorClient = Depends(get_database),
    limit: int = Query(20, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    data_type: Optional[str] = Query(None, description="数据分类")
):
    return await get_zvt_data_logs(db, limit=limit, skip=skip, data_type=data_type)


@router.get("/{_id}", response_model=ZvtDataLogInDB, description="查询ZVT数据日志")
async def get_zvt_data_log_view(
    db: AsyncIOMotorClient = Depends(get_database),
    _id: PyObjectId = Path(...)
):
    try:
        return await get_zvt_data_by_id(db, _id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="未找到该数据.")


# @router.put("/{_id}", response_model=UpdateResult, description="更新ZVT数据日志")
# async def update_zvt_data_log_view(
#     db: AsyncIOMotorClient = Depends(get_database),
#     _id: PyObjectId = Path(...),
#     zvt_data_in_update: ZvtDataLogInUpdate = Body(...)
# ):
#     return await update_zvt_data_log_by_id(db, _id, zvt_data_in_update)


@router.put("/{_id}", response_model=UpdateResult, description="部分更新ZVT数据日志")
async def partial_update_zvt_data_log_view(
    db: AsyncIOMotorClient = Depends(get_database),
    _id: PyObjectId = Path(...),
    zvt_data_in_partial_update: ZvtDataLogInPartialUpdate = Body(...),
):
    return await partial_update_zvt_data_log_by_id(db, _id, **zvt_data_in_partial_update.dict())


@router.delete("/{_id}", response_model=ResultInResponse, description="删除ZVT数据日志")
async def delete_zvt_data_log_view(
    db: AsyncIOMotorClient = Depends(get_database),
    _id: PyObjectId = Path(...),
):
    try:
        return await delete_zvt_data_log_by_id(db, _id)
    except EntityDoesNotExist:
        return HTTPException(status_code=404, detail="未找要删除的数据.")


