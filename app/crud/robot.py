import logging
import warnings
from collections import ChainMap
from datetime import datetime
from typing import List, Optional, Union

import pandas as pd
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReplaceOne
from stralib import FastTdate
from stralib.adam.data_operator import get_assess_result

from app import settings
from app.core.config import get
from app.core.errors import (
    CRUDError,
    DiscuzqCustomError,
    NoActionError,
    NoDataError,
    NoRobotError,
    NoUserError,
    RecordDoesNotExist,
    RobotStatusError,
    TradeDateError,
)
from app.crud.base import (
    get_collection_by_config,
    get_robots_collection,
    get_user_collection,
    get_user_message_collection,
    get_equipment_collection,
)
from app.crud.client_base import get_client_robot_cursor, get_client_robot_list
from app.crud.discuzq import create_thread
from app.crud.equipment import delete_strategy_by_sid, 查询装备列表
from app.crud.permission import 获取某用户的所有权限
from app.crud.profile import get_profile_for_user
from app.crud.real_and_backtest import get_实盘回测_filter
from app.crud.strategy_data import get_strategy_data_list
from app.crud.user import get_user
from app.enums.common import 回测评级数据集, 数据库排序
from app.enums.publish import 策略分类enum
from app.enums.robot import 机器人状态, 机器人状态更新操作类型Enum
from app.enums.user import 消息分类, 消息类型
from app.extentions import logger
from app.models.robot import (
    Robot,
    机器人回测信号,
    机器人回测指标,
    机器人回测评级,
    机器人实盘信号,
    机器人实盘指标,
)
from app.schema.common import ResultInResponse
from app.schema.robot import (
    机器人BaseInUpdate,
    机器人inResponse,
    机器人InUpdate,
    机器人回测信号InCreate,
    机器人回测指标InCreate,
    机器人回测评级InCreate,
    机器人回测详情InResponse,
    机器人实盘信号InCreate,
    机器人实盘指标InCreate,
    机器人推荐InResponse,
    机器人状态InUpdate,
    机器人详情InResponse,
)
from app.schema.user import User, UserMessageInCreate
from app.service.datetime import get_early_morning
from app.service.publish.strategy_publish_log import 创建成功日志
from app.service.robots.robot import 是否被组合使用, 是否被订阅, 计算机器人运行数据
from app.service.strategy_data import 策略数据完整性检验


async def 查询某机器人信息(
    conn: AsyncIOMotorClient,
    sid: str,
    show_detail: bool,
    user: Optional[User] = None,
) -> Union[机器人详情InResponse, 机器人inResponse]:
    """根据sid查询某机器人信息"""
    robot_info = await get_robots_collection(conn).find_one({"标识符": sid})
    if not robot_info:
        raise NoRobotError
    robot = Robot(**robot_info)
    author = await get_profile_for_user(conn, robot.作者)
    result = dict(作者=author)
    result.update(**robot.dict(exclude={"作者"}))
    if show_detail:
        风控包列表 = await 查询装备列表(conn, {"标识符": robot.风控包列表}, 0, 0, [], user=user)
        择时装备列表 = await 查询装备列表(conn, {"标识符": robot.择时装备列表}, 0, 0, [], user=user)
        风控装备列表 = await 查询装备列表(conn, {"标识符": robot.风控装备列表}, 0, 0, [], user=user)
        选股装备列表 = await 查询装备列表(conn, {"标识符": robot.选股装备列表}, 0, 0, [], user=user)
        交易装备列表 = await 查询装备列表(conn, {"标识符": robot.交易装备列表}, 0, 0, [], user=user)
        extra = dict(风控包列表=风控包列表, 择时装备列表=择时装备列表, 风控装备列表=风控装备列表, 选股装备列表=选股装备列表, 交易装备列表=交易装备列表)
        result.update(extra)
        return 机器人详情InResponse(**result)
    else:
        return 机器人inResponse(**result)


async def 查询机器人列表(
    conn: AsyncIOMotorClient,
    query: dict,
    limit: int,
    skip: int,
    order_by: list = None,
    user: User = None,
) -> List[机器人inResponse]:
    db_query = {key: value for key, value in query.items() if value}
    # 因为分类在数据中没有单独字段，所以需要单独处理
    if "标签" in db_query:
        if not isinstance(db_query["标签"], dict):
            db_query["标签"] = {"$in": db_query["标签"]}
    list_cursor = await get_client_robot_cursor(conn, db_query, limit, skip, order_by, user=user)
    response = []
    async for row in list_cursor:
        robot = Robot(**row)
        author = await get_profile_for_user(conn, robot.作者)
        robot = 机器人inResponse(**robot.dict(exclude={"作者"}), 作者=author)
        response.append(robot)
    return response


async def 查询我的机器人列表(conn: AsyncIOMotorClient, 筛选: str, 排序: str, 排序方式: str, user: User) -> List[Robot]:
    robot_query = {"状态": {"$ne": "已删除"}}
    user_permissions = await 获取某用户的所有权限(conn, user)
    if not any(
        [
            "*" in user_permissions.permissions.keys(),
            ("机器人" in user_permissions.permissions.keys() and "查看他人" in user_permissions.permissions["机器人"]),
        ]
    ):
        robot_query["作者"] = user.username
    if 筛选 == "我订阅的机器人":
        robot_query = {
            "状态": {"$ne": "已删除"},
            "标识符": {"$in": user.robot.subscribe_info.focus_list},
        }
    elif 筛选 == "我创建的机器人":
        robot_query["作者"] = user.username
    else:
        if robot_query.get("作者"):
            robot_query.update(
                {
                    "$or": [
                        {"作者": robot_query.pop("作者")},
                        {"标识符": {"$in": user.robot.subscribe_info.focus_list}},
                    ]
                }
            )
    robot_list_cursor = await get_client_robot_cursor(
        conn,
        robot_query,
        limit=0,
        sort=[(排序, 数据库排序[排序方式].value)],
        user=user,
    )
    return [Robot(**row) async for row in robot_list_cursor]


async def 查询是否有该机器人(conn: AsyncIOMotorClient, filters: dict) -> str:
    robot_info = await get_robots_collection(conn).find_one(filters)
    if robot_info:
        return "success"
    else:
        return "failed"


async def 创建机器人(conn: AsyncIOMotorClient, 机器人: Robot, send_message: bool = True) -> 机器人inResponse:
    author = await get_user(conn, 机器人.作者)
    if not author:
        logger.error(f"没有找到名为{机器人.作者}的注册用户，无法创建!")
        raise NoUserError
    robot = Robot(**机器人.dict())
    robot = robot.dict(by_alias=True)
    # 发布文章到社区
    try:
        category = settings.discuzq.category["机器人"]
    except AttributeError:
        category = None
    topic = {
        "title": f"机器人【{机器人.名称}】{机器人.创建时间.strftime('%Y-%m-%d')}创建成功啦",
        "raw": f"机器人【{机器人.名称}】 创建成功啦\n{机器人.简介}",
        "category": category,
    }
    try:
        obj = await create_thread(机器人.作者, **topic)
    except DiscuzqCustomError as e:
        logging.error(f"[发布文章失败]{e}")
    except AttributeError as e:
        logging.error(f"[发布文章失败]{e}")
    else:
        robot["文章标识符"] = obj and obj["id"]
    result = await get_robots_collection(conn).insert_one(robot)
    robot["作者"] = author
    if result.inserted_id:
        if send_message and robot["状态"] == "审核中":
            message = {
                "title": "机器人正在审核",
                "content": f"您的机器人“{机器人.名称}”已开始审核",
                "category": 消息分类.robot,
                "msg_type": 消息类型.review,
                "data_info": 机器人.标识符,
                "username": author.username,
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
        elif send_message and robot["状态"] == "已上线":
            message = {
                "title": "新机器人上线",
                "content": f"{author.username}的新机器人“{机器人.名称}”上线了",
                "category": 消息分类.robot,
                "msg_type": 消息类型.online,
                "data_info": 机器人.标识符,
                "username": author.username,
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
        return 机器人inResponse(**robot)


async def 更新机器人(conn: AsyncIOMotorClient, 标识符: str, 机器人: dict):
    # 更新标识符： 如果缺失必选装备则将标识符调整为15开头
    data = await get_robots_collection(conn).find_one({"标识符": 标识符})
    new_dict = ChainMap(机器人, data)
    if not all([new_dict["选股装备列表"], new_dict["择时装备列表"], new_dict["交易装备列表"]]):
        标识符 = f"15{data['标识符'][2:]}"
        new_dict["标识符"] = 标识符
        new_dict["状态"] = "已上线"
    await get_robots_collection(conn).update_one({"_id": new_dict["_id"]}, {"$set": new_dict})
    return 标识符


async def 修改机器人(conn: AsyncIOMotorClient, 标识符: str, 机器人: 机器人InUpdate) -> ResultInResponse:
    robot_status = await 获取机器人状态(conn, 标识符)
    if robot_status in [机器人状态.已下线, 机器人状态.审核未通过]:
        robot_dict = 机器人.dict(by_alias=True)
        robot_dict["状态"] = "审核中"
    else:
        robot = {k: v for k, v in 机器人.dict().items() if v}
        robot_dict = 机器人BaseInUpdate(**robot).dict(by_alias=True)
    标识符 = await 更新机器人(conn, 标识符, robot_dict)
    robot_info = await 查询某机器人信息(conn, 标识符, show_detail=False)
    if not robot_info:
        logger.error(f"未找到标识符为'{标识符}'的机器人！")
        raise NoRobotError
    if robot_info.状态 == "审核中" and robot_status in ["审核未通过", "已下线"]:
        message = {
            "title": "机器人正在审核",
            "content": f"您的机器人“{robot_info.名称}”已开始审核",
            "category": 消息分类.robot,
            "msg_type": 消息类型.review,
            "data_info": 标识符,
            "username": robot_info.作者.username,
            "created_at": datetime.utcnow(),
        }
        await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
    return ResultInResponse()


async def 获取机器人状态(conn: AsyncIOMotorClient, 标识符: str):
    robot_info = await get_robots_collection(conn).find_one({"标识符": 标识符})
    if robot_info:
        return robot_info["状态"]


async def 修改机器人的运行数据(conn: AsyncIOMotorClient, 标识符: str) -> ResultInResponse:
    机器人状态 = await 获取机器人状态(conn, 标识符)
    if 机器人状态 not in ["已上线", "已下线"]:
        logger.error(f"机器人状态错误, 该状态({机器人状态})不允许修改！")
        raise RobotStatusError
    robot = await 计算机器人运行数据(conn, 标识符)
    if robot:
        robot.pop("计算时间")
        result = await get_robots_collection(conn).update_one({"标识符": 标识符}, {"$set": robot})
        if not result:
            raise RuntimeError("修改机器人失败！")
    return ResultInResponse()


async def 删除某机器人(conn: AsyncIOMotorClient, sid: str) -> int:
    result = await get_robots_collection(conn).delete_one({"标识符": sid})
    await delete_strategy_by_sid(conn, sid)
    return result.deleted_count


async def 获取机器人评价数据(sid: str, start: datetime, end: datetime) -> pd.DataFrame:
    ret_df = get_assess_result(sid, start, end)
    if isinstance(ret_df, pd.DataFrame) and not ret_df.empty:
        return ret_df


async def 获取机器人回测指标数据(
    conn: AsyncIOMotorClient,
    sid: str,
    start: datetime,
    end: datetime,
    limit: int,
    skip: int,
) -> List[机器人回测指标]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    robot_indicator_list_cursor = (
        get_collection_by_config(conn, "机器人回测指标collection名").find(query_doc, limit=limit, skip=skip).sort([("交易日期", pymongo.ASCENDING)])
    )
    response = []
    async for row in robot_indicator_list_cursor:
        robot_indicator = 机器人回测指标(**row)
        response.append(robot_indicator)
    return response


async def 获取机器人回测信号数据(
    conn: AsyncIOMotorClient,
    sid: str,
    start: datetime,
    end: datetime,
    limit: int,
    skip: int,
) -> List[机器人回测信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    robot_indicator_list_cursor = (
        get_collection_by_config(conn, "机器人回测信号collection名").find(query_doc, limit=limit, skip=skip).sort([("交易日期", pymongo.ASCENDING)])
    )
    response = []
    async for row in robot_indicator_list_cursor:
        robot_indicator = 机器人回测信号(**row)
        response.append(robot_indicator)
    return response


async def 获取机器人回测评级数据(conn: AsyncIOMotorClient, sid: str) -> List[机器人回测评级]:
    query_doc = {"标识符": sid}
    robot_assess_list_cursor = get_collection_by_config(conn, "机器人回测评级collection名").find(query_doc)
    response = []
    async for row in robot_assess_list_cursor:
        robot_assess = 机器人回测评级(**row)
        response.append(robot_assess)
    return response


async def 获取机器人某个数据集的回测评级数据(conn: AsyncIOMotorClient, sid: str, 数据集: 回测评级数据集) -> List[机器人回测评级]:
    query_doc = {"标识符": sid, "数据集": 数据集}
    cursor = get_collection_by_config(conn, "机器人回测评级collection名").find(query_doc)
    return [机器人回测评级(**row) async for row in cursor]


async def 获取机器人实盘信号数据(
    conn: AsyncIOMotorClient,
    sid: str,
    start: datetime,
    end: datetime,
    limit: int,
    skip: int,
    排序方式: str,
) -> List[机器人实盘信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    robot_indicator_list_cursor = (
        get_collection_by_config(conn, "机器人实盘信号collection名").find(query_doc, limit=limit, skip=skip).sort([("交易日期", 数据库排序[排序方式].value)])
    )
    response = []
    async for row in robot_indicator_list_cursor:
        robot_indicator = 机器人实盘信号(**row)
        response.append(robot_indicator)
    return response


async def 获取机器人某日实盘信号数据(conn: AsyncIOMotorClient, sid: str, tdate: datetime) -> List[机器人实盘信号]:
    query_doc = {"标识符": sid, "交易日期": tdate}
    robot_indicator_list_cursor = get_collection_by_config(conn, "机器人实盘信号collection名").find(query_doc)
    response = []
    async for row in robot_indicator_list_cursor:
        robot_indicator = 机器人实盘信号(**row)
        response.append(robot_indicator)
    return response


async def 获取最新机器人实盘信号数据(conn: AsyncIOMotorClient, sid: str) -> List[机器人实盘信号]:
    robot_info = await get_robots_collection(conn).find_one({"标识符": sid})
    tdate = get_early_morning(robot_info["下线时间"]) if robot_info["状态"] == 机器人状态.已下线 else get_early_morning()
    robot_indicator = await 获取机器人某日实盘信号数据(conn, sid, tdate)
    if not robot_indicator:
        tdate = FastTdate.last_tdate(tdate)
        robot_indicator = await 获取机器人某日实盘信号数据(conn, sid, tdate)
    if robot_indicator:
        return robot_indicator
    else:
        return list()


async def 获取机器人实盘指标数据(
    conn: AsyncIOMotorClient,
    sid: str,
    start: datetime,
    end: datetime,
    limit: int,
    skip: int,
    order_by: list = None,
) -> List[机器人实盘指标]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    robot_indicator_list_cursor = get_collection_by_config(conn, "机器人实盘指标collection名").find(query_doc, limit=limit, skip=skip, sort=order_by)

    response = []
    async for row in robot_indicator_list_cursor:
        robot_indicator = 机器人实盘指标(**row)
        response.append(robot_indicator)
    return response


async def 获取最新机器人实盘指标数据(conn: AsyncIOMotorClient, sid: str) -> Optional[机器人实盘指标]:
    robot_info = await get_robots_collection(conn).find_one({"标识符": sid})
    上线时间 = robot_info.get("上线时间")
    计算时间 = robot_info.get("计算时间")
    # 刚上线未产生实盘指标数据
    if 上线时间 == 计算时间 or 计算时间 is None:
        return None
    # 上线的机器人，计算时间不更新则认为出现异常
    if 计算时间 < FastTdate.last_tdate(get_early_morning()):
        raise TradeDateError(message=f"[机器人计算时间错误] 不是最新的计算时间")
    query_doc = {"标识符": sid, "交易日期": 计算时间}
    robot_indicator = await get_collection_by_config(conn, "机器人实盘指标collection名").find_one(query_doc)
    if robot_indicator:
        return 机器人实盘指标(**robot_indicator)
    raise NoDataError(message=f"未获取到日期为{计算时间:%Y-%m-%d}的机器人实盘指标数据")


async def 获取机器人回测详情数据(conn: AsyncIOMotorClient, sid: str, 数据集: 回测评级数据集) -> 机器人回测详情InResponse:
    query_doc = {"标识符": sid, "数据集": 数据集}
    robot_assess = await get_collection_by_config(conn, "机器人回测评级collection名").find_one(query_doc)
    query_doc = {"标识符": sid, "交易日期": robot_assess.get("结束时间", None)}
    robot_indicator = await get_collection_by_config(conn, "机器人回测指标collection名").find_one(query_doc)
    robot_signal = get_collection_by_config(conn, "机器人回测信号collection名").find(query_doc)
    robot_signal = [row async for row in robot_signal]
    return 机器人回测详情InResponse(机器人回测指标详情=robot_indicator, 机器人回测评级详情=robot_assess, 机器人回测信号详情=robot_signal)


async def 创建机器人实盘回测数据(
    conn: AsyncIOMotorClient,
    collectionName: str,
    机器人实盘回测数据: List[
        Union[
            机器人回测指标InCreate,
            机器人回测信号InCreate,
            机器人回测评级InCreate,
            机器人实盘信号InCreate,
            机器人实盘指标InCreate,
        ]
    ],
) -> ResultInResponse:
    warnings.warn("已存在更新版本的函数，该函数后续不再维护", DeprecationWarning)
    async with await conn.start_session() as s:
        async with s.start_transaction():
            strategy_type, strategy_name = get(collectionName).split(".")
            await 策略数据完整性检验(conn, strategy_name, strategy_type, 机器人实盘回测数据)
            if isinstance(机器人实盘回测数据[0], 机器人回测评级InCreate):
                await 刷新机器人评级(conn, 机器人实盘回测数据)
            replace_list = [
                ReplaceOne(
                    get_实盘回测_filter(collectionName, x),
                    x.dict(by_alias=True),
                    upsert=True,
                )
                for x in 机器人实盘回测数据
            ]
            await get_collection_by_config(conn, collectionName).bulk_write(replace_list)
            for obj in 机器人实盘回测数据:
                if hasattr(obj, "交易日期"):
                    tdate = obj.交易日期
                else:
                    tdate = get_early_morning()
                await 创建成功日志(conn, 策略分类enum.机器人, obj.标识符, tdate)
            return ResultInResponse()


async def 刷新机器人评级(conn: AsyncIOMotorClient, 机器人回测评级列表: List[机器人回测评级InCreate]):
    update_list, insert_list, created_at = [], [], datetime.utcnow()
    for 回测评级 in 机器人回测评级列表:
        if 回测评级.数据集 != "整体评级":
            continue
        robot = await get_robots_collection(conn).find_one({"标识符": 回测评级.标识符})
        robot["评级"] = 回测评级.评级
        robot["计算时间"] = None
        if robot["评级"] in ["A", "B", "C", "D"]:
            robot["状态"] = "已上线"
            robot["上线时间"] = get_early_morning()
            message = UserMessageInCreate(
                **{
                    "title": "新机器人上线",
                    "content": f"{robot['作者']}的新机器人“{robot['名称']}”上线了",
                    "category": 消息分类.robot,
                    "msg_type": 消息类型.online,
                    "data_info": 回测评级.标识符,
                    "username": robot["作者"],
                    "created_at": created_at,
                }
            ).dict()
            if message not in insert_list:
                insert_list.append(message)
        else:
            robot["状态"] = "审核未通过"
        tmp = ReplaceOne({"标识符": 回测评级.标识符}, robot)
        update_list.append(tmp)
        kwargs = UserMessageInCreate(
            **{
                "title": "机器人审核已结束",
                "content": f"您的机器人“{robot['名称']}”已结束审核，审核结果为{回测评级.评级}",
                "category": 消息分类.robot,
                "msg_type": 消息类型.review,
                "data_info": 回测评级.标识符,
                "username": robot["作者"],
                "created_at": created_at,
            }
        ).dict()
        if kwargs not in insert_list:
            insert_list.append(kwargs)
    if update_list:
        await get_robots_collection(conn).bulk_write(update_list)
        get_user_message_collection(conn).insert_many(insert_list)


async def 更新机器人状态(conn: AsyncIOMotorClient, sid: str, robot_state_in_update: 机器人状态InUpdate):
    """
    上线：
        状态：
            审核未通过->审核中
            已下线->审核中
    下线：
        状态：已上线->已下线
    删除：
        状态：
            审核未通过->已删除
            已下线->已删除
    :param conn:
    :param sid:
    :param robot_state_in_update:
    :return:

    Parameters
    ----------
    """
    robot_info = await get_robots_collection(conn).find_one({"标识符": sid})
    if not robot_info:
        raise NoRobotError
    if robot_state_in_update.操作类型 == 机器人状态更新操作类型Enum.上线:
        if robot_info["状态"] not in ["已下线", "审核未通过"]:
            raise RobotStatusError(message="原状态不允许切换")
        if await 是否被组合使用(sid, conn):
            raise CRUDError(message="当前机器人被组合使用中，无法上线审核")
        filters = {"状态": "审核中", "下线时间": None} if sid.startswith("10") else {"状态": "已上线", "下线时间": None}
    elif robot_state_in_update.操作类型 == 机器人状态更新操作类型Enum.下线:
        if robot_info["状态"] != "已上线":
            raise RobotStatusError(message="原状态不允许切换")
        if await 是否被组合使用(sid, conn):
            raise CRUDError(message="当前机器人被组合使用中，无法下线")
        filters = {"状态": "已下线", "下线时间": datetime.utcnow()}
        filters.update({"下线原因": robot_state_in_update.原因})
    elif robot_state_in_update.操作类型 == 机器人状态更新操作类型Enum.删除:
        if sid.startswith("10") and robot_info["状态"] not in ["已下线", "审核未通过"]:
            raise RobotStatusError(message="原状态不允许切换")
        if await 是否被订阅(sid, conn):
            raise CRUDError(message="当前机器人被订阅中，无法删除")
        filters = {"状态": "已删除"}
    else:
        raise NoActionError
    result = await get_robots_collection(conn).update_one({"标识符": sid}, {"$set": filters})
    if result:
        if filters["状态"] == "已删除":
            await delete_strategy_by_sid(conn, sid)
        if filters["状态"] == "审核中":
            message = {
                "title": "机器人正在审核",
                "content": f"您的机器人“{robot_info['名称']}”已开始审核",
                "category": 消息分类.robot,
                "msg_type": 消息类型.review,
                "data_info": sid,
                "username": robot_info["作者"],
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
        if filters["状态"] == "已下线":
            users_cursor = get_user_collection(conn).find({"robot": {"$elemMatch": {"标识符": sid}}})
            messages = [
                UserMessageInCreate(
                    **{
                        "title": "下线通知",
                        "content": f"您订阅的“{robot_info['名称']}”机器人已经下线进行优化，优化期间您仍可以收到该机器人的信号",
                        "category": 消息分类.robot,
                        "msg_type": 消息类型.offline,
                        "data_info": sid,
                        "username": user["username"],
                        "created_at": datetime.utcnow(),
                    }
                ).dict()
                async for user in users_cursor
            ]
            get_user_message_collection(conn).insert_many(messages)
        return ResultInResponse()
    else:
        raise CRUDError(message="更新机器人状态失败！")


async def 更新某机器人计算时间(conn: AsyncIOMotorClient, sid: str, 计算时间: datetime) -> ResultInResponse:
    result = await get_robots_collection(conn).update_one({"标识符": sid}, {"$set": {"计算时间": 计算时间}})
    if result.matched_count == 1:
        return ResultInResponse()
    else:
        raise CRUDError(message=f"更新计算时间失败！")


async def get_robot(sid: str, db: AsyncIOMotorClient):
    result = await get_robots_collection(db).find_one({"标识符": sid})
    if result:
        result["作者"] = await get_profile_for_user(db, result["作者"])
    else:
        raise NoRobotError
    robot = 机器人inResponse(**result)
    return robot


async def 优选推荐机器人(conn: AsyncIOMotorClient, user: User = None) -> List[机器人推荐InResponse]:
    交易日期 = FastTdate.last_tdate(get_early_morning(datetime.utcnow()))
    real_indicator_list = await get_strategy_data_list(conn, "机器人实盘指标collection名", {"交易日期": 交易日期}, sort=[("年化收益率", -1)])
    if not real_indicator_list:
        raise RecordDoesNotExist(message="查询机器人实盘指标错误,未查询到存在实盘指标的机器人")
    robot_list = await get_client_robot_list(conn, {"标识符": {"$in": [x["标识符"] for x in real_indicator_list]}}, user)
    if not robot_list:
        raise RecordDoesNotExist(message="查询机器人错误, 未查询到符合要求的机器人")

    popular_robot = robot_list[0]
    max_annualized = real_indicator_list[0]
    min_drawdown = min(real_indicator_list, key=lambda x: x["最大回撤"])
    max_popular = list(filter(lambda x: x["标识符"] == popular_robot["标识符"], real_indicator_list))[0]
    max_annualized_robot = list(filter(lambda x: x["标识符"] == max_annualized["标识符"], robot_list))[0]
    min_drawdown_robot = list(filter(lambda x: x["标识符"] == min_drawdown["标识符"], robot_list))[0]

    人气最高 = 机器人推荐InResponse(
        robot=Robot(**popular_robot),
        real_indicator=机器人实盘指标(**max_popular),
        reason=f"累计服务人数",
    )
    收益最高 = 机器人推荐InResponse(
        robot=Robot(**max_annualized_robot),
        real_indicator=机器人实盘指标(**max_annualized),
        reason=f"年化收益率",
    )
    回撤最小 = 机器人推荐InResponse(
        robot=Robot(**min_drawdown_robot),
        real_indicator=机器人实盘指标(**min_drawdown),
        reason=f"最大回撤",
    )
    return [人气最高, 收益最高, 回撤最小]


async def 推荐列表(
    conn: AsyncIOMotorClient,
    query: dict,
    limit: int,
    skip: int,
    order_by: list,
    trade_date: datetime,
    user: User = None,
) -> List[机器人推荐InResponse]:
    db_query = {key: value for key, value in query.items() if value}
    交易日期 = FastTdate.last_tdate(get_early_morning(datetime.utcnow())) if not trade_date else FastTdate.last_tdate(get_early_morning(trade_date))
    robot_list_cursor = await get_client_robot_cursor(conn, db_query, limit=limit, skip=skip, user=user)
    result = []
    async for row in robot_list_cursor:
        实盘指标 = await get_collection_by_config(conn, "机器人实盘指标collection名").find_one({"交易日期": 交易日期, "标识符": row["标识符"]})
        if 实盘指标:
            result.append(机器人推荐InResponse(robot=Robot(**row), real_indicator=机器人实盘指标(**实盘指标)))
    if order_by[0] == "评级":
        result = sorted(
            result,
            key=lambda x: (x.robot.评级, -x.real_indicator.年化收益率),
            reverse=True if order_by[1] == "倒序" else False,
        )
    elif order_by[0] == "累计服务人数":
        result.sort(key=lambda x: x.robot.累计服务人数, reverse=True if order_by[1] == "倒序" else False)
    elif order_by[0] == "累计收益率":
        result.sort(
            key=lambda x: x.real_indicator.累计收益率,
            reverse=True if order_by[1] == "倒序" else False,
        )
    elif order_by[0] == "最大回撤":
        result.sort(
            key=lambda x: x.real_indicator.最大回撤,
            reverse=False if order_by[1] == "倒序" else True,
        )
    return result


async def get_robot_user_list(conn: AsyncIOMotorClient, query: dict, limit: int, skip: int) -> List[str]:
    db_query = {key: value for key, value in query.items() if value}
    robot_list_cursor = get_robots_collection(conn).find(db_query, limit=limit, skip=skip)
    auths = {robot.get("作者") async for robot in robot_list_cursor}
    user_cursor = get_user_collection(conn).find({"username": {"$in": list(auths)}})
    return list({user.get("nickname") async for user in user_cursor})


async def check_strategy_exist(conn: AsyncIOMotorClient, username: str):
    e_num = await get_equipment_collection(conn).count_documents({"作者": username})
    r_num = await get_robots_collection(conn).count_documents({"作者": username})
    return True if e_num + r_num else False
