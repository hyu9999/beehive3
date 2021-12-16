import logging
from datetime import datetime
from typing import List, Union

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReplaceOne
from stralib import FastTdate
from stralib.adam.data_operator import get_strategy_signal

from app import settings
from app.core.config import get
from app.core.errors import NoEquipError, EquipStatusError, NoActionError, CRUDError, DiscuzqCustomError, EquipNameExistError
from app.crud.base import get_equipment_collection, get_collection_by_config, get_user_collection, get_user_message_collection
from app.crud.client_base import get_client_equipment_cursor
from app.crud.discuzq import create_thread
from app.crud.permission import 获取某用户的所有权限
from app.crud.profile import get_profile_for_user
from app.crud.real_and_backtest import get_实盘回测_filter
from app.enums.common import 回测评级数据集, 数据库排序
from app.enums.equipment import 装备分类_3, 装备状态, EquipmentCollectionName, 装备状态更新操作类型Enum
from app.enums.user import 消息类型, 消息分类
from app.extentions import logger
from app.models.equipment import (
    选股装备回测信号,
    选股装备回测指标,
    择时装备回测信号,
    择时装备回测指标,
    择时装备回测评级,
    选股装备实盘信号,
    择时装备实盘信号,
    选股装备实盘指标,
    择时装备实盘指标,
    Equipment,
    大类资产配置回测信号,
    基金定投回测信号,
    大类资产配置回测评级,
    大类资产配置回测指标,
    基金定投回测指标,
    基金定投回测评级,
    大类资产配置实盘信号,
    基金定投实盘信号,
    大类资产配置实盘指标,
    基金定投实盘指标,
)
from app.models.equipment import 选股装备回测评级
from app.schema.common import ResultInResponse
from app.schema.equipment import (
    装备InResponse,
    装备InUpdate,
    择时装备回测信号InCreate,
    择时装备回测指标InCreate,
    择时装备回测评级InCreate,
    择时装备实盘信号InCreate,
    择时装备实盘指标InCreate,
    选股装备回测信号InCreate,
    选股装备回测指标InCreate,
    选股装备回测评级InCreate,
    装备BaseInUpdate,
    大类资产配置回测信号InCreate,
    大类资产配置回测指标InCreate,
    大类资产配置回测评级InCreate,
    大类资产配置实盘信号InCreate,
    大类资产配置实盘指标InCreate,
    基金定投回测信号InCreate,
    基金定投回测指标InCreate,
    基金定投回测评级InCreate,
    基金定投实盘指标InCreate,
    基金定投实盘信号InCreate,
    装备状态InUpdate,
    装备运行数据InUpdate,
)
from app.schema.user import UserMessageInCreate, User
from app.service.datetime import get_early_morning
from app.service.equipment import 是否被机器人使用, 是否被机器人订阅, 计算装备运行数据
from app.service.publish.strategy_publish_log import 创建成功日志, 查询策略分类
from app.service.strategy_data import 策略数据完整性检验


async def 查询装备列表(conn: AsyncIOMotorClient, equipment_query: dict, limit: int, skip: int, 排序: list, user=None) -> List[装备InResponse]:
    db_query = {key: value for key, value in equipment_query.items() if value}
    if "标识符" in db_query:
        db_query["标识符"] = {"$in": db_query["标识符"]}
    list_cursor = await get_client_equipment_cursor(conn, db_query, limit, skip, 排序, user=user)
    response = []
    async for row in list_cursor:
        row["作者"] = await get_profile_for_user(conn, row["作者"])
        equipment = 装备InResponse(**row)
        response.append(equipment)
    return response


async def 查询我的装备列表(conn: AsyncIOMotorClient, 筛选: str, 排序: str, 排序方式: str, user: User, 分类: 装备分类_3 = None) -> List[Equipment]:
    equipment_query = {"状态": {"$ne": "已删除"}, "分类": 分类 if 分类 else {"$ne": 分类}}
    user_permissions = await 获取某用户的所有权限(conn, user)
    if not any(["*" in user_permissions.permissions.keys(), ("装备" in user_permissions.permissions.keys() and "查看他人" in user_permissions.permissions["装备"])]):
        equipment_query["作者"] = user.username
    if 筛选 == "我订阅的装备":
        equipment_query = {"状态": {"$ne": "已删除"}, "标识符": {"$in": user.equipment.subscribe_info.focus_list}, "分类": 分类 if 分类 else {"$ne": 分类}}
    elif 筛选 == "我创建的装备":
        equipment_query["作者"] = user.username
    else:
        if equipment_query.get("作者"):
            equipment_query.update({"$or": [{"作者": equipment_query.pop("作者")}, {"标识符": {"$in": user.equipment.subscribe_info.focus_list}}]})
    equipment_list_cursor = await get_client_equipment_cursor(conn, equipment_query, limit=0, sort=[(排序, 数据库排序[排序方式].value)], user=user)
    return [Equipment(**row) async for row in equipment_list_cursor]


async def 查询是否有该装备(conn: AsyncIOMotorClient, filters: dict) -> str:
    equipment_info = await get_equipment_collection(conn).find_one(filters)
    if equipment_info:
        result = "success"
    else:
        result = "failed"
    return result


async def 查询某个装备的详情(conn: AsyncIOMotorClient, sid: str) -> 装备InResponse:
    equipment_info = await get_equipment_collection(conn).find_one({"标识符": sid})
    if equipment_info:
        equipment_info["作者"] = await get_profile_for_user(conn, equipment_info["作者"])
        if sid.startswith("02") and not equipment_info.get("最佳调仓周期"):
            equipment_info["最佳调仓周期"] = await 查询并更新选股装备最佳调仓周期(conn, sid)
        return 装备InResponse(**equipment_info)


async def 新建装备(conn: AsyncIOMotorClient, 装备: Equipment):
    equipment_dict = 装备.dict(by_alias=True)
    if 装备.分类 == "风控包":
        equipment_dict["评级"] = "A"
        equipment_dict["计算时间"] = get_early_morning()
    # 发布文章到社区
    topic = {"title": f"装备【{装备.名称}】{装备.创建时间.strftime('%Y-%m-%d')}上线啦", "raw": f"装备【{装备.名称}】 创建成功啦\n{装备.简介}", "category": settings.discuzq.category["装备"]}
    try:
        obj = await create_thread(装备.作者, **topic)
    except DiscuzqCustomError as e:
        logging.error(f"[发布文章失败] {e}")
    else:
        equipment_dict["文章标识符"] = obj and obj["id"]
    result = await get_equipment_collection(conn).insert_one(equipment_dict)
    if result:
        equipment_dict["作者"] = await get_profile_for_user(conn, 装备.作者)
        # 发送消息
        if equipment_dict["状态"] == "审核中":
            message = {
                "title": "装备正在审核",
                "content": f"您的装备“{装备.名称}”已开始审核",
                "category": 消息分类.equipment,
                "msg_type": 消息类型.review,
                "data_info": 装备.标识符,
                "username": 装备.作者,
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
        return 装备InResponse(**equipment_dict)
    else:
        raise CRUDError(message="创建装备失败！")


async def 更新装备(conn: AsyncIOMotorClient, 标识符: str, 装备: dict):
    update_dict = {k: v for k, v in 装备.items() if v}
    if update_dict:
        result = await get_equipment_collection(conn).update_one({"标识符": 标识符}, {"$set": update_dict})
        return result


async def 获取装备状态(conn: AsyncIOMotorClient, 标识符: str):
    equipment_info = await get_equipment_collection(conn).find_one({"标识符": 标识符})
    if equipment_info:
        return equipment_info["状态"]


async def 更新装备的某个字段(conn: AsyncIOMotorClient, 标识符: str, 装备: 装备InUpdate):
    equipment_status = await 获取装备状态(conn, 标识符)
    # 检查装备名称是否重复
    if 装备.名称:
        if await 查询是否有该装备(conn, {"名称": 装备.名称, "标识符": {"$ne": 标识符}}) == "success":
            raise EquipNameExistError

    if equipment_status in ["审核未通过", "已下线"]:
        装备Dict = 装备.dict(by_alias=True)
        装备Dict["状态"] = "审核中"
    else:
        equipment = {k: v for k, v in 装备.dict().items() if v}
        装备Dict = 装备BaseInUpdate(**equipment).dict(by_alias=True)
    await 更新装备(conn, 标识符, 装备Dict)
    response = await 查询某个装备的详情(conn, 标识符)
    if not response:
        logger.error(f"未找到标识符为'{标识符}'的装备！")
        raise NoEquipError
    if response.状态 == "审核中" and equipment_status in ["审核未通过", "已下线"]:
        message = {
            "title": "装备正在审核",
            "content": f"您的装备“{response.名称}”已开始审核",
            "category": 消息分类.equipment,
            "msg_type": 消息类型.review,
            "data_info": 标识符,
            "username": response.作者.username,
            "created_at": datetime.utcnow(),
        }
        await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
    return response


async def 更新装备的运行数据(conn: AsyncIOMotorClient, 标识符: str, 装备: 装备运行数据InUpdate):
    装备状态 = await 获取装备状态(conn, 标识符)
    if 装备状态 not in ["已上线", "已下线"]:
        raise EquipStatusError(message=f"该状态不允许修改！")
    if settings.manufacturer_switch:
        result = await 更新装备(conn, 标识符, 装备.dict(by_alias=True))
    else:
        运行数据 = await 计算装备运行数据(conn, 标识符)
        运行数据.pop("计算时间")
        result = await get_equipment_collection(conn).update_one({"标识符": 标识符}, {"$set": 运行数据})
    if result:
        return ResultInResponse()


async def 更新包状态(conn: AsyncIOMotorClient, sid: str, equipment_state_in_update: 装备状态InUpdate):
    """
    创建装备：
        状态:
            创建中->已上线
    ...............上线...................
    装备下线：
        状态：已上线->已下线
    装备上线：
        状态：已下线->已上线
    装备删除：
        状态：已下线->已删除
    """
    package_info = await get_equipment_collection(conn).find_one({"标识符": sid})
    if equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.创建装备:
        if package_info["状态"] is not None:
            raise EquipStatusError(message=f"原状态不允许切换")
        filters = {"状态": "已上线"}
    elif equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.装备上线:
        if package_info["状态"] != "已下线":
            raise EquipStatusError(message=f"原状态不允许切换")
        filters = {"状态": "已上线", "下线时间": None}
    elif equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.装备下线:
        if package_info["状态"] != "已上线":
            raise EquipStatusError(message=f"原状态不允许切换")
        if await 是否被机器人使用(sid, conn):
            raise EquipStatusError(message="该装备被机器人使用，无法下线！")
        filters = {"状态": "已下线"}
        filters.update({"下线原因": equipment_state_in_update.原因})
    elif equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.装备删除:
        if package_info["状态"] != "已下线":
            raise EquipStatusError(message=f"原状态不允许切换")
        if await 是否被机器人订阅(sid, conn):
            raise CRUDError(message="该装备被机器人订阅，无法删除！")
        filters = {"状态": "已删除"}
    else:
        raise NoActionError
    result = await get_equipment_collection(conn).update_one({"标识符": sid}, {"$set": filters})
    if result:
        if filters["状态"] == "审核中":
            message = {
                "title": "装备正在审核",
                "content": f"您的装备“{package_info['名称']}”已开始审核",
                "category": 消息分类.equipment,
                "msg_type": 消息类型.review,
                "data_info": sid,
                "username": package_info["作者"],
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
        if filters["状态"] == "已下线":
            users_cursor = get_user_collection(conn).find({"equipment": {"$elemMatch": {"标识符": sid}}})
            messages = [
                UserMessageInCreate(
                    **{
                        "title": "下线通知",
                        "content": f"您订阅的“{package_info['名称']}”装备已经下线进行优化，优化期间您仍可以收到该装备的信号",
                        "category": 消息分类.equipment,
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
        raise CRUDError(message="更新包状态失败！")


async def 更新装备状态(conn: AsyncIOMotorClient, sid: str, equipment_state_in_update: 装备状态InUpdate):
    """
    信号审核（手动传入）：
        状态:未审核->审核中
    ...............上线...................
    装备上线：
        状态：
            审核未通过->审核中
            已下线->审核中
    装备下线：
        状态：已上线->已下线
    装备删除：
        状态：
            审核未通过->已删除
            已下线->已删除
    :param conn:
    :param sid:
    :param name:
    :return:
    """
    equipment_info = await get_equipment_collection(conn).find_one({"标识符": sid})
    if not equipment_info:
        raise NoEquipError
    if equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.装备上线:
        if equipment_info["状态"] not in ["审核未通过", "已下线"]:
            raise EquipStatusError(message=f"原状态不允许切换")
        filters = {"状态": "审核中", "下线时间": None}
    elif equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.信号审核:
        if equipment_info["状态"] != "未审核":
            raise EquipStatusError(message=f"原状态不允许切换")
        filters = {"状态": "审核中"}
    elif equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.装备下线:
        if equipment_info["状态"] != "已上线":
            raise EquipStatusError(message=f"原状态不允许切换")
        if await 是否被机器人使用(sid, conn):
            raise CRUDError(message="该装备被机器人使用，无法下线！")
        filters = {"状态": "已下线", "下线时间": datetime.utcnow()}
        filters.update({"下线原因": equipment_state_in_update.原因})
    elif equipment_state_in_update.操作类型 == 装备状态更新操作类型Enum.装备删除:
        if equipment_info["状态"] not in ["已下线", "审核未通过"]:
            raise EquipStatusError
        if await 是否被机器人订阅(sid, conn):
            raise CRUDError(message="该装备被机器人订阅，无法删除！")
        filters = {"状态": "已删除"}
    else:
        raise NoActionError
    result = await get_equipment_collection(conn).update_one({"标识符": sid}, {"$set": filters})
    if result:
        if filters["状态"] == "已删除":
            await delete_strategy_by_sid(conn, sid)
        if filters["状态"] == "审核中":
            message = {
                "title": "装备正在审核",
                "content": f"您的装备“{equipment_info['名称']}”已开始审核",
                "category": 消息分类.equipment,
                "msg_type": 消息类型.review,
                "data_info": sid,
                "username": equipment_info["作者"],
                "created_at": datetime.utcnow(),
            }
            await get_user_message_collection(conn).insert_one(UserMessageInCreate(**message).dict())
        if filters["状态"] == "已下线":
            users_cursor = get_user_collection(conn).find({"equipment": {"$elemMatch": {"标识符": sid}}})
            messages = [
                UserMessageInCreate(
                    **{
                        "title": "下线通知",
                        "content": f"您订阅的“{equipment_info['名称']}”装备已经下线进行优化，优化期间您仍可以收到该装备的信号",
                        "category": 消息分类.equipment,
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
        raise CRUDError(message="更新装备状态失败！")


async def 删除某装备(conn: AsyncIOMotorClient, sid: str):
    await delete_strategy_by_sid(conn, sid)
    return await get_equipment_collection(conn).delete_one({"标识符": sid})


async def 获取某装备的信号(sid: str, start: datetime, end: datetime) -> pd.DataFrame:
    ret_df = get_strategy_signal(sid, start, end)
    return ret_df


async def 获取选股回测信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[选股装备回测信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "选股回测信号collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in signal_list_cursor:
        signal = 选股装备回测信号(**row)
        response.append(signal)
    response_sort = sorted(response, key=lambda x: x.交易日期)
    return response_sort


async def 获取选股回测指标数据(conn: AsyncIOMotorClient, sid: str) -> List[选股装备回测指标]:
    query_doc = {"标识符": sid}
    indicator_list_cursor = get_collection_by_config(conn, "选股回测指标collection名").find(query_doc)
    response = []
    async for row in indicator_list_cursor:
        indicator = 选股装备回测指标(**row)
        response.append(indicator)
    return response


async def 获取选股回测评级数据(conn: AsyncIOMotorClient, sid: str) -> List[选股装备回测评级]:
    query_doc = {"标识符": sid}
    assess_list_cursor = get_collection_by_config(conn, "选股回测评级collection名").find(query_doc)
    response = []
    async for row in assess_list_cursor:
        assess = 选股装备回测评级(**row)
        response.append(assess)
    return response


async def 获取择时回测信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[择时装备回测信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "择时回测信号collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in signal_list_cursor:
        signal = 择时装备回测信号(**row)
        response.append(signal)
    response_sort = sorted(response, key=lambda x: x.交易日期)
    return response_sort


async def 获取择时回测指标数据(conn: AsyncIOMotorClient, sid: str, symbol: str, 回测年份: str) -> List[择时装备回测指标]:
    query_doc = {"标识符": sid, "标的指数": symbol}
    if 回测年份:
        query_doc["回测年份"] = 回测年份
    indicator_list_cursor = get_collection_by_config(conn, "择时回测指标collection名").find(query_doc)
    response = []
    async for row in indicator_list_cursor:
        indicator = 择时装备回测指标(**row)
        response.append(indicator)
    return response


async def 获取择时回测评级数据(conn: AsyncIOMotorClient, sid: str, symbol: str) -> List[择时装备回测评级]:
    query_doc = {"标识符": sid, "标的指数": symbol}
    assess_list_cursor = get_collection_by_config(conn, "择时回测评级collection名").find(query_doc)
    response = []
    async for row in assess_list_cursor:
        assess = 择时装备回测评级(**row)
        response.append(assess)
    return response


async def 获取选股实盘信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[选股装备实盘信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "选股实盘信号collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in signal_list_cursor:
        signal = 选股装备实盘信号(**row)
        response.append(signal)
    response_sort = sorted(response, key=lambda x: x.交易日期)
    return response_sort


async def 获取择时实盘信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[择时装备实盘信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "择时实盘信号collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in signal_list_cursor:
        signal = 择时装备实盘信号(**row)
        response.append(signal)
    response_sort = sorted(response, key=lambda x: x.交易日期)
    return response_sort


async def 获取选股实盘指标数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[选股装备实盘指标]:
    query_doc = {"标识符": sid, "结束时间": {"$gte": start, "$lte": end}}
    indicator_list_cursor = get_collection_by_config(conn, "选股实盘指标collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in indicator_list_cursor:
        indicator = 选股装备实盘指标(**row)
        response.append(indicator)
    response_sort = sorted(response, key=lambda x: x.结束时间)
    return response_sort


async def 获取择时实盘指标数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[择时装备实盘指标]:
    query_doc = {"标识符": sid, "结束时间": {"$gte": start, "$lte": end}}
    indicator_list_cursor = get_collection_by_config(conn, "择时实盘指标collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in indicator_list_cursor:
        indicator = 择时装备实盘指标(**row)
        response.append(indicator)
    response_sort = sorted(response, key=lambda x: x.结束时间)
    return response_sort


async def 获取某数据集选股回测评级详情(conn: AsyncIOMotorClient, sid: str, 数据集: 回测评级数据集) -> 选股装备回测评级:
    query_doc = {"标识符": sid, "数据集": 数据集}
    row = await get_collection_by_config(conn, "选股回测评级collection名").find_one(query_doc)
    if row:
        return 选股装备回测评级(**row)


async def 获取某数据集基金定投回测评级详情(conn: AsyncIOMotorClient, sid: str, 数据集: 回测评级数据集) -> 基金定投回测评级:
    query_doc = {"标识符": sid, "数据集": 数据集}
    row = await get_collection_by_config(conn, "基金定投回测评级collection名").find_one(query_doc)
    if row:
        return 基金定投回测评级(**row)


async def 获取某数据集大类资产配置回测评级详情(conn: AsyncIOMotorClient, sid: str, 数据集: 回测评级数据集) -> 大类资产配置回测评级:
    query_doc = {"标识符": sid, "数据集": 数据集}
    row = await get_collection_by_config(conn, "大类资产配置回测评级collection名").find_one(query_doc)
    if row:
        return 大类资产配置回测评级(**row)


async def 获取某交易日选股回测指标(conn: AsyncIOMotorClient, sid: str, 交易日期: datetime) -> 选股装备回测指标:
    query_doc = {"标识符": sid, "结束时间": 交易日期}
    row = await get_collection_by_config(conn, "选股回测指标collection名").find_one(query_doc)
    if row:
        return 选股装备回测指标(**row)


async def 获取某交易日选股回测信号(conn: AsyncIOMotorClient, sid: str, 交易日期: datetime) -> 选股装备回测信号:
    query_doc = {"标识符": sid, "交易日期": 交易日期}
    row = await get_collection_by_config(conn, "选股回测信号collection名").find_one(query_doc)
    if row:
        return 选股装备回测信号(**row)


async def 创建装备实盘回测数据(
    conn: AsyncIOMotorClient,
    collectionName: str,
    装备实盘回测数据: List[
        Union[
            择时装备回测信号InCreate,
            择时装备回测指标InCreate,
            择时装备回测评级InCreate,
            择时装备实盘信号InCreate,
            择时装备实盘指标InCreate,
            选股装备回测信号InCreate,
            选股装备回测指标InCreate,
            选股装备回测评级InCreate,
            大类资产配置回测信号InCreate,
            大类资产配置回测指标InCreate,
            大类资产配置回测评级InCreate,
            大类资产配置实盘信号InCreate,
            大类资产配置实盘指标InCreate,
            基金定投回测信号InCreate,
            基金定投回测指标InCreate,
            基金定投回测评级InCreate,
            基金定投实盘信号InCreate,
            基金定投实盘指标InCreate,
        ]
    ],
) -> ResultInResponse:
    async with await conn.start_session() as s:
        async with s.start_transaction():
            strategy_type, strategy_name = get(collectionName).split(".")
            strategy_name = strategy_name[:-2] if strategy_name.endswith("装备") else strategy_name
            await 策略数据完整性检验(conn, strategy_name, strategy_type, 装备实盘回测数据)
            if isinstance(装备实盘回测数据[0], 择时装备回测评级InCreate):
                await 刷新择时装备评级(conn, 装备实盘回测数据)
            elif isinstance(装备实盘回测数据[0], 选股装备回测评级InCreate) or isinstance(装备实盘回测数据[0], 大类资产配置回测评级InCreate) or isinstance(装备实盘回测数据[0], 基金定投回测评级InCreate):
                await 刷新选股_大类资产_基金定投评级(conn, 装备实盘回测数据)
            replace_list = [ReplaceOne(get_实盘回测_filter(collectionName, x), x.dict(by_alias=True), upsert=True) for x in 装备实盘回测数据]
            await get_collection_by_config(conn, collectionName).bulk_write(replace_list)
            for obj in 装备实盘回测数据:
                交易日期 = obj.交易日期 if hasattr(obj, "交易日期") else get_early_morning()
                await 创建成功日志(conn, 查询策略分类(collectionName), obj.标识符, 交易日期)
            return ResultInResponse()


async def 刷新择时装备评级(conn: AsyncIOMotorClient, 择时装备回测评级列表: List[择时装备回测评级InCreate]):
    update_list, insert_list, created_at = [], [], datetime.utcnow()
    for 回测评级 in 择时装备回测评级列表:
        if not all([回测评级.回测年份 == "全部", 回测评级.标的指数 == "399001"]):
            continue
        equipment = await get_equipment_collection(conn).find_one({"标识符": 回测评级.标识符})
        equipment["评级"] = 回测评级.评级
        equipment["计算时间"] = None
        if equipment["评级"] in ["A", "B", "C", "D"]:
            equipment["状态"] = "已上线"
            equipment["上线时间"] = get_early_morning()
            message = UserMessageInCreate(
                **{
                    "title": "新装备上线",
                    "content": f"{equipment['作者']}的新装备“{equipment['名称']}”上线了",
                    "category": 消息分类.equipment,
                    "msg_type": 消息类型.online,
                    "data_info": 回测评级.标识符,
                    "username": equipment["作者"],
                    "created_at": created_at,
                }
            ).dict()
            if message not in insert_list:
                insert_list.append(message)
        else:
            equipment["状态"] = "审核未通过"
        tmp = ReplaceOne({"标识符": 回测评级.标识符}, equipment)
        update_list.append(tmp)
        kwargs = UserMessageInCreate(
            **{
                "title": "装备审核已结束",
                "content": f"您的装备“{equipment['名称']}”已结束审核，审核结果为{equipment['评级']}",
                "category": 消息分类.equipment,
                "msg_type": 消息类型.review,
                "data_info": 回测评级.标识符,
                "username": equipment["作者"],
                "created_at": created_at,
            }
        ).dict()
        if kwargs not in insert_list:
            insert_list.append(kwargs)
    if update_list:
        await get_equipment_collection(conn).bulk_write(update_list)
        get_user_message_collection(conn).insert_many(insert_list)


async def 刷新选股_大类资产_基金定投评级(conn: AsyncIOMotorClient, 选股_大类资产_基金定投回测评级列表: List[Union[大类资产配置回测评级InCreate, 基金定投回测评级InCreate, 选股装备回测评级InCreate]]):
    update_list, insert_list, created_at = [], [], datetime.utcnow()
    for 回测评级 in 选股_大类资产_基金定投回测评级列表:
        if 回测评级.数据集 != "整体评级":
            continue
        equipment = await get_equipment_collection(conn).find_one({"标识符": 回测评级.标识符})
        equipment["评级"] = 回测评级.评级
        equipment["计算时间"] = None
        if equipment["评级"] in ["A", "B", "C", "D"]:
            equipment["状态"] = "已上线"
            equipment["上线时间"] = get_early_morning()
            message = UserMessageInCreate(
                **{
                    "title": "新装备上线",
                    "content": f"{equipment['作者']}的新装备“{equipment['名称']}”上线了",
                    "category": 消息分类.equipment,
                    "msg_type": 消息类型.online,
                    "data_info": 回测评级.标识符,
                    "username": equipment["作者"],
                    "created_at": created_at,
                }
            ).dict()
            if message not in insert_list:
                insert_list.append(message)
        else:
            equipment["状态"] = "审核未通过"
        tmp = ReplaceOne({"标识符": 回测评级.标识符}, equipment)
        update_list.append(tmp)
        kwargs = UserMessageInCreate(
            **{
                "title": "装备审核已结束",
                "content": f"您的装备“{equipment['名称']}”已结束审核，审核结果为{equipment['评级']}",
                "category": 消息分类.equipment,
                "msg_type": 消息类型.review,
                "data_info": 回测评级.标识符,
                "username": equipment["作者"],
                "created_at": created_at,
            }
        ).dict()
        if kwargs not in insert_list:
            insert_list.append(kwargs)
    if update_list:
        await get_equipment_collection(conn).bulk_write(update_list)
        get_user_message_collection(conn).insert_many(insert_list)


async def 更新某装备计算时间(conn: AsyncIOMotorClient, sid: str, 计算时间: datetime) -> ResultInResponse:
    result = await get_equipment_collection(conn).update_one({"标识符": sid}, {"$set": {"计算时间": 计算时间}})
    if result.matched_count == 1:
        return ResultInResponse()
    else:
        raise CRUDError(message=f"更新计算时间失败！")


async def get_equipment_user_list(conn: AsyncIOMotorClient, query: dict, limit: int, skip: int) -> List[str]:
    db_query = {key: value for key, value in query.items() if value}
    equipment_list_cursor = get_equipment_collection(conn).find(db_query, limit=limit, skip=skip)
    auths = {equipment.get("作者") async for equipment in equipment_list_cursor}
    user_cursor = get_user_collection(conn).find({"username": {"$in": list(auths)}})
    return list({user.get("nickname") async for user in user_cursor})


async def 获取大类资产配置回测信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[大类资产配置回测信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "大类资产配置回测信号collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in signal_list_cursor:
        signal = 大类资产配置回测信号(**row)
        response.append(signal)
    response_sort = sorted(response, key=lambda x: x.交易日期)
    return response_sort


async def 获取大类资产配置回测指标数据(conn: AsyncIOMotorClient, sid: str) -> List[大类资产配置回测指标]:
    query_doc = {"标识符": sid}
    indicator_list_cursor = get_collection_by_config(conn, "大类资产配置回测指标collection名").find(query_doc)
    response = []
    async for row in indicator_list_cursor:
        indicator = 大类资产配置回测指标(**row)
        response.append(indicator)
    return response


async def 获取大类资产配置回测评级数据(conn: AsyncIOMotorClient, sid: str) -> List[大类资产配置回测评级]:
    query_doc = {"标识符": sid}
    assess_list_cursor = get_collection_by_config(conn, "大类资产配置回测评级collection名").find(query_doc)
    response = []
    async for row in assess_list_cursor:
        assess = 大类资产配置回测评级(**row)
        response.append(assess)
    return response


async def 获取大类资产配置实盘信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int, sort: list) -> List[大类资产配置实盘信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "大类资产配置实盘信号collection名").find(query_doc, limit=limit, skip=skip, sort=sort)
    return [大类资产配置实盘信号(**row) async for row in signal_list_cursor]


async def 获取大类资产配置实盘指标数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int, sort: list) -> List[大类资产配置实盘指标]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "大类资产配置实盘指标collection名").find(query_doc, limit=limit, skip=skip, sort=sort)
    return [大类资产配置实盘指标(**row) async for row in signal_list_cursor]


async def 获取基金定投回测信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int) -> List[基金定投回测信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "基金定投回测信号collection名").find(query_doc, limit=limit, skip=skip)
    response = []
    async for row in signal_list_cursor:
        signal = 基金定投回测信号(**row)
        response.append(signal)
    response_sort = sorted(response, key=lambda x: x.交易日期)
    return response_sort


async def 获取基金定投回测指标数据(conn: AsyncIOMotorClient, sid: str) -> List[基金定投回测指标]:
    query_doc = {"标识符": sid}
    indicator_list_cursor = get_collection_by_config(conn, "基金定投回测指标collection名").find(query_doc)
    response = []
    async for row in indicator_list_cursor:
        indicator = 基金定投回测指标(**row)
        response.append(indicator)
    return response


async def 获取基金定投回测评级数据(conn: AsyncIOMotorClient, sid: str) -> List[基金定投回测评级]:
    query_doc = {"标识符": sid}
    assess_list_cursor = get_collection_by_config(conn, "基金定投回测评级collection名").find(query_doc)
    response = []
    async for row in assess_list_cursor:
        assess = 基金定投回测评级(**row)
        response.append(assess)
    return response


async def 获取基金定投实盘信号数据(conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int, sort: list) -> List[基金定投实盘信号]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    signal_list_cursor = get_collection_by_config(conn, "基金定投实盘信号collection名").find(query_doc, limit=limit, skip=skip, sort=sort)
    return [基金定投实盘信号(**row) async for row in signal_list_cursor]


async def 获取某装备实盘指标数据(
    conn: AsyncIOMotorClient, sid: str, start: datetime, end: datetime, limit: int, skip: int, sort: list = [("交易日期", 1)]
) -> List[Union[大类资产配置实盘指标, 基金定投实盘指标]]:
    query_doc = {"标识符": sid, "交易日期": {"$gte": start, "$lte": end}}
    if sid.startswith("06"):
        indicator_list_cursor = get_collection_by_config(conn, "大类资产配置实盘指标collection名").find(query_doc, limit=limit, skip=skip, sort=sort)
        return [大类资产配置实盘指标(**row) async for row in indicator_list_cursor]
    elif sid.startswith("07"):
        indicator_list_cursor = get_collection_by_config(conn, "基金定投实盘指标collection名").find(query_doc, limit=limit, skip=skip, sort=sort)
        return [基金定投实盘指标(**row) async for row in indicator_list_cursor]


async def 获取某装备最新实盘数据(conn: AsyncIOMotorClient, sid: str, real_type: str) -> Union[大类资产配置实盘指标, 基金定投实盘指标, List[大类资产配置实盘信号], List[基金定投实盘信号]]:
    equipment_info = await get_equipment_collection(conn).find_one({"标识符": sid})
    tdate = get_early_morning(equipment_info["下线时间"]) if equipment_info["状态"] == 装备状态.已下线 else get_early_morning()
    query_doc = {"标识符": sid, "交易日期": tdate}
    if sid.startswith("06"):
        collection_name = EquipmentCollectionName.asset_allocation.value[real_type].value
        if real_type == "real_indicator":
            equipment_real_indicator = await get_collection_by_config(conn, collection_name).find_one(query_doc)
            if equipment_real_indicator:
                result = 大类资产配置实盘指标(**equipment_real_indicator)
            else:
                query_doc["交易日期"] = FastTdate.last_tdate(tdate)
                equipment_real_indicator = await get_collection_by_config(conn, collection_name).find_one(query_doc)
                result = 大类资产配置实盘指标(**equipment_real_indicator)
            return result
        else:
            equipment_real_signal = get_collection_by_config(conn, collection_name).find(query_doc)
            result = [大类资产配置实盘信号(**row) async for row in equipment_real_signal]
            if not result:
                query_doc["交易日期"] = FastTdate.last_tdate(tdate)
                equipment_real_signal = get_collection_by_config(conn, collection_name).find(query_doc)
                result = [大类资产配置实盘信号(**row) async for row in equipment_real_signal]
            return result
    elif sid.startswith("07"):
        collection_name = EquipmentCollectionName.aipman.value[real_type].value
        if real_type == "real_indicator":
            equipment_real_indicator = await get_collection_by_config(conn, collection_name).find_one(query_doc)
            if equipment_real_indicator:
                result = 基金定投实盘指标(**equipment_real_indicator)
            else:
                query_doc["交易日期"] = FastTdate.last_tdate(tdate)
                equipment_real_indicator = await get_collection_by_config(conn, collection_name).find_one(query_doc)
                result = 基金定投实盘指标(**equipment_real_indicator)
            return result
        else:
            equipment_real_signal = get_collection_by_config(conn, collection_name).find(query_doc)
            result = [基金定投实盘信号(**row) async for row in equipment_real_signal]
            if not result:
                query_doc["交易日期"] = FastTdate.last_tdate(tdate)
                equipment_real_signal = get_collection_by_config(conn, collection_name).find(query_doc)
            result = [基金定投实盘信号(**row) async for row in equipment_real_signal]
        return result


async def 删除某装备实盘回测数据(conn: AsyncIOMotorClient, collection_name: str, sid: str) -> ResultInResponse:
    query_doc = {"标识符": sid}
    await get_collection_by_config(conn, collection_name).delete_many(query_doc)
    return ResultInResponse()


async def delete_strategy_by_sid(conn: AsyncIOMotorClient, sid: str):
    """根据给定标识符，删除中文表中和其相关的所有数据."""
    collection_name_list = [
        "机器人回测指标collection名",
        "机器人回测信号collection名",
        "机器人回测评级collection名",
        "机器人实盘信号collection名",
        "机器人实盘指标collection名",
        "择时回测信号collection名",
        "选股回测信号collection名",
        "择时回测指标collection名",
        "选股回测指标collection名",
        "择时回测评级collection名",
        "选股回测评级collection名",
        "择时实盘信号collection名",
        "选股实盘信号collection名",
    ]
    for collection_name in collection_name_list:
        await get_collection_by_config(conn, collection_name).find_one_and_delete({"标识符": sid})


async def 查询并更新选股装备最佳调仓周期(conn: AsyncIOMotorClient, sid: str):
    data = await get_collection_by_config(conn, "选股回测指标collection名").find_one({"标识符": sid, "数据集": "整体评级"})
    if data:
        await get_equipment_collection(conn).update_one({"标识符": sid}, {"$set": {"最佳调仓周期": data["最佳调仓周期"]}})
        return data["最佳调仓周期"]
