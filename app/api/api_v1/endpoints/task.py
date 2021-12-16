from datetime import datetime

from fastapi import APIRouter, Body, Depends, Query, Security
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.background import BackgroundTasks

from app.core.jwt import get_current_user_authorizer
from app.db.mongodb import get_database
from app.outer_sys.wechat.user import get_wechat_avatar
from app.schedulers.ability.func import (
    calculate_simulated_trading_portfolio_ability_task,
)
from app.schedulers.disc.func import fill_disc_data
from app.schedulers.operation_data.func import update_strategy_calculate_datetime
from app.schedulers.publish.func import write_strategy_publish_log_task
from app.schedulers.time_series_data.func import (
    save_simulated_trading_portfolio_time_series_data_task,
)
from app.schedulers.wechat.func import sync_wechat_avatar_task
from app.schema.common import ResultInResponse

router = APIRouter()


@router.post("/fill_disc_data", response_model=ResultInResponse, description="补充社区数据")
async def fill_disc_data_task_view(
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["后台任务:执行"]),
):
    background_tasks.add_task(fill_disc_data, db)
    return ResultInResponse()


@router.post("/update_wechat_avatar", response_model=ResultInResponse, description="更新微信头像到用户表")
async def update_wechat_avatar_task_view(
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["后台任务:执行"]),
):
    background_tasks.add_task(sync_wechat_avatar_task, db)
    return ResultInResponse()


@router.post("/cal_abi", description="战斗力计算")
async def cal_view(
    background_tasks: BackgroundTasks,
    start_date: datetime = Body(None, embed=True),
    end_date: datetime = Body(None, embed=True),
    filters: dict = Body(..., embed=True),
    _=Security(get_current_user_authorizer(), scopes=["后台任务:执行"]),
):
    background_tasks.add_task(
        calculate_simulated_trading_portfolio_ability_task,
        filters,
        start_date=start_date,
        end_date=end_date,
    )
    return ResultInResponse()


@router.post("/syc_acc", description="同步流水")
async def sync_acc_data_view(
    background_tasks: BackgroundTasks,
    portfolio_id: str = Body(None, description="组合id", embed=True),
    _=Security(get_current_user_authorizer(), scopes=["后台任务:执行"]),
):
    background_tasks.add_task(
        save_simulated_trading_portfolio_time_series_data_task,
        portfolio_id=portfolio_id,
    )
    return ResultInResponse()


@router.post("/update_strategy_calculate_datetime", description="更新计算时间")
async def update_strategy_calculate_datetime_view(
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorClient = Depends(get_database),
    tdate: datetime = Query(None),
    _=Security(get_current_user_authorizer(), scopes=["后台任务:执行"]),
):
    background_tasks.add_task(update_strategy_calculate_datetime, db, tdate=tdate)
    return ResultInResponse()


@router.post("/write_strategy_publish_log_task", description="策略数据发布")
async def write_strategy_publish_log_view(
    background_tasks: BackgroundTasks,
    username: str = Query(None),
    tdate: datetime = Query(None),
    _=Security(get_current_user_authorizer(), scopes=["后台任务:执行"]),
):
    background_tasks.add_task(write_strategy_publish_log_task, tdate=tdate, username=username)
    return ResultInResponse()


@router.get("/avatar", description="获取用户头像")
async def avatar_get_view(
    open_id: str = Query(None, description=""),
):
    dt = get_wechat_avatar(open_id)
    return ResultInResponse(result=dt)
