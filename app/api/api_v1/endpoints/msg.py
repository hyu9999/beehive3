from typing import List

from fastapi import APIRouter, Body, Depends, Security, HTTPException, Query, Path
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.jwt import get_current_user_authorizer
from app.crud.msg import (
    create_msg_config,
    delete_msg_config_by_id,
    update_msg_config_by_id,
    patch_msg_config_by_id,
    get_msg_config_by_id,
    get_msg_configs,
)
from app.db.mongodb import get_database
from app.enums.user import 消息类型
from app.models.msg import MessageConfig
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.msg import MessageConfigInCreate, MessageConfigInUpdate, MessageConfigInResponse

router = APIRouter()


@router.post("", response_model=MessageConfig, description="创建消息配置")
async def create_msg_config_view(
    msg_config: MessageConfigInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["消息:创建"]),
):
    try:
        return await create_msg_config(db, msg_config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建消息配置失败，错误信息: {e}")


@router.delete("/{id}", response_model=ResultInResponse, description="删除消息配置")
async def delete_msg_config_view(
    id: PyObjectId = Path(..., description="msg_config_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["消息:删除"]),
):
    try:
        return await delete_msg_config_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除消息配置失败，错误信息: {e}")


@router.put("/{id}", response_model=UpdateResult, description="全量更新消息配置")
async def update_msg_config_view(
    id: PyObjectId = Path(..., description="msg_config_id"),
    msg_config: MessageConfigInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["消息:修改"]),
):
    try:
        return await update_msg_config_by_id(db, id, msg_config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新消息配置失败，错误信息: {e}")


@router.patch("/{id}", response_model=UpdateResult, description="部分更新消息配置")
async def patch_msg_config_view(
    id: PyObjectId = Path(..., description="msg_config_id"),
    msg_config: MessageConfigInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["消息:修改"]),
):
    try:
        return await patch_msg_config_by_id(db, id, msg_config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新消息配置失败，错误信息: {e}")


@router.get("/{id}", response_model=MessageConfigInResponse, description="获取消息配置")
async def get_msg_config_view(
    id: PyObjectId = Path(..., description="msg_config_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["消息:查看"]),
):
    try:
        return await get_msg_config_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取消息配置失败，错误信息: {e}")


@router.get("/list", response_model=List[MessageConfigInResponse], description="获取消息配置列表")
async def get_msg_configs_view(
    title: str = Query(None),
    category: 消息类型 = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["消息:查看"]),
):
    try:
        db_query = {"category": category, "title": title}
        return await get_msg_configs(db, db_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取消息配置列表失败，错误信息: {e}")
