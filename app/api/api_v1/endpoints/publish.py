from typing import List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Query, Depends, Path
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.errors import NoRobotError
from app.crud.equipment import 查询某个装备的详情
from app.crud.publish import find_strategy_publish_log, get_strategy_daily_logs, get_daily_log_today
from app.crud.robot import 查询某机器人信息
from app.crud.user import get_user_by_username
from app.db.mongodb import get_database
from app.enums.publish import 发布情况enum, 策略分类enum, 策略状态enum
from app.models.publish import StrategyDailyLogInDB, StrategyPublishLogInDB

router = APIRouter()


@router.get("/manufacturer/log", response_model=List[StrategyPublishLogInDB], description="当日数据完整性检查")
async def get_manufacturer_logs(
    username: Optional[str] = Query(None, description="厂商用户名"),
    db: AsyncIOMotorClient = Depends(get_database),
    开始时间: Optional[date] = Query(None, title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    结束时间: Optional[date] = Query(None, title="开始时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15."),
    是否完成发布: Optional[bool] = Query(None, description="是否完成发布"),
):
    if 开始时间 is not None:
        开始时间 = datetime.combine(开始时间, datetime.min.time())
    if 结束时间 is not None:
        结束时间 = datetime.combine(结束时间, datetime.min.time())
    return await find_strategy_publish_log(db, 开始时间, 结束时间, username, 是否完成发布)


@router.get("/strategy/log", response_model=List[StrategyDailyLogInDB], description="策略日志列表")
async def get_daily_logs(
    db: AsyncIOMotorClient = Depends(get_database),
    username: Optional[str] = Query(None, description="厂商用户名"),
    发布情况: Optional[发布情况enum] = Query(None),
    分类: Optional[策略分类enum] = Query(None),
    状态: Optional[策略状态enum] = Query(None),
    标识符: Optional[str] = Query(None),
    开始日期: Optional[date] = Query(None, title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    结束日期: Optional[date] = Query(None, title="开始时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15."),
):
    if 开始日期 is not None:
        开始日期 = datetime.combine(开始日期, datetime.min.time())
    if 结束日期 is not None:
        结束日期 = datetime.combine(结束日期, datetime.min.time())
    logs = await get_strategy_daily_logs(db, 发布情况=发布情况, 分类=分类, 标识符=标识符, 开始日期=开始日期,
                                         结束日期=结束日期)
    results = logs
    if username is not None:
        results = []
        user = await get_user_by_username(db, username)
        sid_list = user.client.robot + user.client.equipment
        for log in logs:
            if log.标识符 in sid_list:
                results.append(log)
    if 状态 is not None:
        logs = results
        results = []
        for log in logs:
            try:
                robot = await 查询某机器人信息(db, log.标识符, show_detail=False)
            except NoRobotError:
                ...
            else:
                if robot and robot.状态 == 状态:
                    results.append(log)
            equipment = await 查询某个装备的详情(db, log.标识符)
            if equipment and equipment.状态 == 状态:
                results.append(log)
    return results


@router.get("/strategy/log/{sid}", response_model=StrategyDailyLogInDB)
async def get_daily_log_today_view(
    db: AsyncIOMotorClient = Depends(get_database),
    sid: str = Path(..., description="标识符"),
):
    return await get_daily_log_today(db, sid)
