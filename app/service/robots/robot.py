import time
from datetime import datetime
from typing import List, Dict

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.core.errors import RobotTooMany
from app.crud.base import (
    get_robots_collection,
    get_collection_by_config,
    get_portfolio_collection,
    get_user_collection,
    get_equipment_collection,
    get_fund_time_series_data_collection,
)
from app.enums.equipment import 装备状态
from app.enums.robot import 机器人状态
from app.models.base.robot import 机器人运行数据
from app.models.robot import Robot
from app.schema.user import User
from app.service.datetime import get_early_morning


async def 生成机器人标识符(db: AsyncIOMotorClient, start_index: int = 10):
    prefix = f"{start_index}{int(time.mktime(datetime.utcnow().timetuple()))}"
    suffix = "1"
    filters = {"标识符": {"$regex": f"^{prefix}.*"}}
    cnt = await get_robots_collection(db).count_documents(filters)
    if cnt:
        queryset = get_robots_collection(db).find(filters).sort("标识符", pymongo.DESCENDING)
        async for x in queryset:
            suffix = int(x["标识符"][-2:]) + 1
            break
    标识符 = f"{prefix}{str(suffix).zfill(2)}"
    return 标识符


async def 机器人数量限制(user: User, db: AsyncIOMotorClient):
    """检查用户机器人数量是否超出限制"""
    if not user.roles[0] == "超级用户":
        filters = {"作者": user.username, "状态": {"$nin": ["已删除", "临时回测"]}}
        cnt = await get_robots_collection(db).count_documents(filters)
        if cnt >= settings.num_limit[user.roles[0]]["robot"]:
            raise RobotTooMany


async def 是否被组合使用(sid: str, db: AsyncIOMotorClient):
    robot = await get_robots_collection(db).find_one({"标识符": sid})
    if robot["管理了多少组合"] > 0:
        return True
    return False


async def 是否被订阅(sid: str, db: AsyncIOMotorClient):
    robot = await get_robots_collection(db).find_one({"标识符": sid})
    if robot["订阅人数"] > 0:
        return True
    return False


async def 获取风控装备列表(风控包标识符列表: List, db: AsyncIOMotorClient):
    packages = get_robots_collection(db).find({"标识符": {"$in": 风控包标识符列表}})
    data = []
    async for pkg in packages:
        data.extend(pkg["装备列表"])
    return data


async def 计算机器人运行数据(db: AsyncIOMotorClient, 标识符: str) -> Dict:
    """

    Parameters
    ----------
    db
    标识符

    Returns
    -------
    机器人运行数据
    """
    data = 机器人运行数据()
    filters = {"标识符": 标识符}
    robot = await get_robots_collection(db).find_one(filters)
    symbol_list = await get_collection_by_config(db, "机器人实盘信号collection名").distinct("证券代码", filters)
    data.分析了多少支股票 = len(symbol_list)
    data.运行天数 = (get_early_morning() - robot["上线时间"]).days
    data.累计产生信号数 = await get_collection_by_config(db, "机器人实盘信号collection名").count_documents(filters)
    实盘指标 = await get_collection_by_config(db, "机器人实盘指标collection名").find_one({"标识符": 标识符, "交易日期": get_early_morning()})
    if 实盘指标:
        data.累计收益率 = 实盘指标["累计收益率"]
    data.管理了多少组合 = await get_portfolio_collection(db).count_documents({"robot": 标识符})
    user_list = await get_portfolio_collection(db).distinct("username", {"robot": 标识符})
    data.累计服务人数 = len(user_list)
    portfolio_id_list = await get_portfolio_collection(db).distinct("_id", {"robot": 标识符})
    fund_ts_cursor = get_fund_time_series_data_collection(db).find({"portfolio": {"$in": portfolio_id_list}, "tdate": get_early_morning()})
    data.累计管理资金 = sum([x["fundbal"] + x["mkval"] async for x in fund_ts_cursor])
    portfolio_cursor = get_portfolio_collection(db).find({"robot": 标识符})
    data.累计创造收益 = data.累计管理资金 - sum([x["initial_funding"] async for x in portfolio_cursor])
    return data.dict()


async def generate_robot_version(robot: Robot, db: AsyncIOMotorClient) -> str:
    """根据传入修改后的机器人来生成新的机器人版本号.

    Returns
    ----------
    version: str
        机器人版本号由三位数字构成, 例如 `1.2.3` .
        首位数字(即 `1` )代表主版本号.
        第二位数字(即 `2` )代表次版本号.
        第三位数字(即 `3` )代表修订号.
    """
    robot_dict = robot.dict()
    MAJOR_FIELDS = set([])
    MINOR_FIELDS = set([])
    AMENDMENT_FIELDS = set([])
    (
        major,
        minor,
        amendment,
    ) = map(int, robot.版本.split("."))
    robot_in_db = await get_robots_collection(db).find_one({"标识符": robot.标识符})
    changed_fields = set([field for field in robot_dict if field in robot_in_db and robot_dict[field] == robot_in_db[field]])
    if changed_fields & MAJOR_FIELDS:
        return f"{major+1}.0.0"
    elif changed_fields & MINOR_FIELDS:
        return f"{major}.{minor+1}.0"
    elif changed_fields & AMENDMENT_FIELDS:
        return f"{major}.{minor}.{amendment+1}"
    else:
        raise robot.版本


async def get_robot_and_equipment(conn: AsyncIOMotorClient, tdate: datetime):
    """获取所有有效的装备和机器人"""
    if settings.manufacturer_switch:
        if not settings.mfrs.CLIENT_USER:
            raise RuntimeError("未配置厂商用户，请联系管理员")
        user = await get_user_collection(conn).find_one({"$or": [{"username": settings.mfrs.CLIENT_USER}, {"mobile": settings.mfrs.CLIENT_USER}]})
        client = user.get("client", {})
        return client.get("robot", []), client.get("equipment", [])
    else:
        robots = [
            r["标识符"] async for r in get_robots_collection(conn).find({"状态": {"$in": [机器人状态.已上线, 机器人状态.已下线]}, "计算时间": {"$ne": tdate}, "标识符": {"$regex": f"^10"}})
        ]
        equipments = [
            e["标识符"] async for e in get_equipment_collection(conn).find({"装备库版本": {"$ne": "3.3"}, "状态": {"$in": [装备状态.已上线, 装备状态.已下线]}, "计算时间": {"$ne": tdate}})
        ]
        return robots, equipments
