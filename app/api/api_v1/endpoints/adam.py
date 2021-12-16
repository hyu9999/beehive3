from datetime import datetime

from fastapi import APIRouter, Security, Depends, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.responses import StreamingResponse
from stralib import get_strategy_signal, get_strategy_flow

from app.core.jwt import get_current_user_authorizer
from app.db.mongodb import get_database
from app.extentions import logger
from app.service.datetime import get_early_morning
from app.service.df import generator_streamer
from app.service.permission import check_robot_permission, check_equipment_permission

router = APIRouter()


@router.get("/signal/", description="查询策略信号")
async def get_adam_signal(
    sid: str = Query(..., description="标识符"),
    start_datetime: datetime = Query(None, description="开始时间"),
    end_datetime: datetime = Query(None, description="结束时间"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    if sid.startswith("10"):
        check_robot_permission(sid, user)
    elif sid.startswith("0"):
        check_equipment_permission(sid, user)
    start_datetime = start_datetime or get_early_morning()
    end_datetime = end_datetime or get_early_morning()
    try:
        df = get_strategy_signal(sid, start_datetime, end_datetime)
    except Exception as e:
        logger.error(f"[查询装备({sid})信号失败] {e}")
        raise HTTPException(status_code=400, detail=f"查询装备列表发生错误，错误信息: {e}")
    return StreamingResponse(generator_streamer(df))


@router.get("/flow/", description="查询机器人流水数据")
async def get_adam_flow(
    sid: str = Query(..., description="标识符"),
    start_datetime: datetime = Query(None, description="开始时间"),
    end_datetime: datetime = Query(None, description="结束时间"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    check_robot_permission(sid, user)
    start_datetime = start_datetime or get_early_morning()
    end_datetime = end_datetime or get_early_morning()
    try:
        df = get_strategy_flow(sid, start_datetime, end_datetime)
    except Exception as e:
        logger.error(f"[查询机器人({sid})流水失败] {e}")
        raise HTTPException(status_code=400, detail=f"查询机器人列表发生错误，错误信息: {e}")
    return StreamingResponse(generator_streamer(df))
