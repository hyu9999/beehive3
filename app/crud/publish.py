from typing import List, Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app.models.publish import StrategyDailyLogInDB, StrategyPublishLogInDB
from app.models.rwmodel import PyObjectId
from app.crud.base import get_strategy_daily_log_collection, get_strategy_publish_log_collection
from app.enums.publish import 发布情况enum, 策略分类enum
from app.schema.publish import StrategyDailyLogInCreate
from app.service.datetime import get_early_morning


async def get_strategy_daily_logs(
    conn: AsyncIOMotorClient,
    *,
    标识符: Optional[str] = None,
    分类: Optional[策略分类enum] = None,
    交易日期: Optional[datetime] = None,
    发布情况: Optional[发布情况enum] = None,
    开始日期: Optional[datetime] = None,
    结束日期: Optional[datetime] = None,
) -> List[StrategyDailyLogInDB]:
    query = {}
    if 分类 is not None:
        query["分类"] = 分类
    if 标识符 is not None:
        query["标识符"] = 标识符
    if 交易日期 is not None:
        query["交易日期"] = 交易日期
    if 发布情况 is not None:
        query["发布情况"] = 发布情况
    if 开始日期 is not None:
        query["交易日期"] = {"$gte": 开始日期}
    if 结束日期 is not None:
        query["交易日期"] = {"$lte": 结束日期}
    if 开始日期 and 结束日期:
        query["交易日期"] = {"$gte": 开始日期, "$lte": 结束日期}
    cursor = get_strategy_daily_log_collection(conn).find(query)
    return [StrategyDailyLogInDB(**log) async for log in cursor]


async def get_strategy_daily_log(
    conn: AsyncIOMotorClient,
    分类: 策略分类enum,
    标识符: str,
    交易日期: datetime
) -> StrategyDailyLogInDB:
    row = await get_strategy_daily_log_collection(conn).find_one({"分类": 分类, "标识符": 标识符, "交易日期": 交易日期})
    if row:
        return StrategyDailyLogInDB(**row)


async def replace_strategy_daily_log_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
    strategy_daily_log: StrategyDailyLogInCreate,
) -> int:
    result = await get_strategy_daily_log_collection(conn).replace_one({"_id": _id}, strategy_daily_log.dict())
    return result.modified_count


async def create_strategy_daily_log(
    conn: AsyncIOMotorClient,
    strategy_daily_log: StrategyDailyLogInCreate,
) -> StrategyDailyLogInDB:
    row = await get_strategy_daily_log_collection(conn).insert_one(strategy_daily_log.dict(exclude={"id"}))
    log = StrategyDailyLogInDB(**strategy_daily_log.dict())
    log.id = row.inserted_id
    return log


async def update_strategy_daily_error_log_by_id(
    conn: AsyncIOMotorClient,
    _id: PyObjectId,
    strategy_daily_log: StrategyDailyLogInCreate,
) -> None:
    await get_strategy_daily_log_collection(conn).update_one(
        {"_id": _id}, {"$push": {"错误信息": strategy_daily_log.错误信息[0].dict()}}
    )


async def find_strategy_publish_log(
    conn: AsyncIOMotorClient,
    start: datetime,
    end: datetime,
    username: str,
    is_completed: bool
) -> List[StrategyPublishLogInDB]:
    query_doc = {}
    if username is not None:
        query_doc["username"] = username
    if start is not None:
        query_doc["交易日期"] = {"$gte": start}
    if end is not None:
        query_doc["交易日期"] = {"$lte": end}
    if start and end:
        query_doc["交易日期"] = {"$gte": start, "$lte": end}
    if is_completed is not None:
        query_doc["是否完成发布"] = is_completed
    rows = get_strategy_publish_log_collection(conn).find(query_doc)
    return [StrategyPublishLogInDB(**row) async for row in rows]


async def get_daily_log_today(
    conn: AsyncIOMotorClient,
    sid: str
) -> StrategyDailyLogInDB:
    row = await get_strategy_daily_log_collection(conn).find_one({"标识符": sid, "交易日期": get_early_morning()})
    if row:
        return StrategyDailyLogInDB(**row)
