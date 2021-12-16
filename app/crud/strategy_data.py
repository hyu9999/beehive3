from typing import List

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReplaceOne
from stralib import FastTdate

from app.crud.base import get_collection_by_config
from app.crud.equipment import 刷新择时装备评级, 刷新选股_大类资产_基金定投评级
from app.enums.equipment import 装备状态
from app.enums.strategy_data import 策略名称, 策略数据类型
from app.models.equipment import 择时装备回测评级, 选股装备回测评级
from app.models.strategy_data import 大类资产配置回测评级, 基金定投回测评级
from app.models.strategy_data import 机器人回测评级
from app.schema.common import ResultInResponse
from app.schema.strategy_data import StrategyInCreate
from app.service.datetime import get_early_morning
from app.service.publish.strategy_publish_log import 创建成功日志
from app.service.strategy_data import get_strategy_model_by_name, 策略数据完整性检验


async def 创建策略数据(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, strategy_data: List[dict]) -> ResultInResponse:
    class_model = get_strategy_model_by_name(strategy_name, strategy_type)
    strategy_obj = [class_model(**x) for x in strategy_data]
    async with await conn.start_session() as s:
        async with s.start_transaction():
            if not strategy_name.机器人:
                await 策略数据完整性检验(conn, strategy_name, strategy_type, strategy_obj)
            if isinstance(strategy_obj[0], 择时装备回测评级):
                await 刷新择时装备评级(conn, strategy_obj)
            elif isinstance(strategy_obj[0], 选股装备回测评级) or isinstance(strategy_obj[0], 大类资产配置回测评级) or isinstance(strategy_obj[0], 基金定投回测评级):
                await 刷新选股_大类资产_基金定投评级(conn, strategy_obj)
            elif isinstance(strategy_obj[0], 机器人回测评级):
                from app.crud.robot import 刷新机器人评级

                await 刷新机器人评级(conn, strategy_obj)
            col_name = f"{strategy_name}{strategy_type}collection名"
            replace_list = [ReplaceOne(get_composite_key_by_strategy_col_name(col_name, x), x.dict(by_alias=True), upsert=True) for x in strategy_obj]
            await get_collection_by_config(conn, col_name).bulk_write(replace_list)
            for obj in strategy_obj:
                交易日期 = obj.交易日期 if hasattr(obj, "交易日期") else get_early_morning()
                await 创建成功日志(conn, strategy_name, obj.标识符, 交易日期)
            return ResultInResponse()


async def 查询策略数据(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, filters: dict, limit: int, skip: int, sort: list):
    col_name = f"{strategy_name}{strategy_type}collection名"
    future = get_collection_by_config(conn, col_name).find(filters, limit=limit, skip=skip)
    if sort:
        future = future.sort(sort)
    class_model = get_strategy_model_by_name(strategy_name, strategy_type)
    return [class_model(**x) async for x in future]


async def 删除策略数据(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, filters: dict):
    col_name = f"{strategy_name}{strategy_type}collection名"
    await get_collection_by_config(conn, col_name).delete_many(filters)
    return ResultInResponse()


def get_composite_key_by_strategy_col_name(
    collection_name: str,
    data: StrategyInCreate,
):
    """
    根据传入的策略表名称获取该表的联合主键

    Parameters
    ----------
    collection_name
    data

    Returns
    -------

    """
    ret_data = {"标识符": data.标识符}
    if collection_name in [
        "选股回测信号collection名",
        "选股实盘信号collection名",
        "机器人回测指标collection名",
        "机器人实盘指标collection名",
        "大类资产配置回测指标collection名",
        "基金定投回测指标collection名",
        "大类资产配置实盘指标collection名",
        "基金定投实盘指标collection名",
    ]:
        ret_data = {"标识符": data.标识符, "交易日期": data.交易日期}
    elif collection_name in ["选股回测指标collection名"]:
        ret_data = {"标识符": data.标识符, "开始时间": data.开始时间, "结束时间": data.结束时间}
    elif collection_name in ["择时回测信号collection名", "择时实盘信号collection名"]:
        ret_data = {"标识符": data.标识符, "交易日期": data.交易日期, "标的指数": data.标的指数}
    elif collection_name in ["择时回测指标collection名", "择时回测评级collection名"]:
        ret_data = {"标识符": data.标识符, "标的指数": data.标的指数, "回测年份": data.回测年份}
    elif collection_name in ["选股回测评级collection名", "机器人回测评级collection名", "大类资产配置回测评级collection名", "基金定投回测评级collection名"]:
        ret_data = {"标识符": data.标识符, "数据集": data.数据集}
    elif collection_name in [
        "机器人回测信号collection名",
        "机器人实盘信号collection名",
        "大类资产配置回测信号collection名",
        "基金定投回测信号collection名",
        "大类资产配置实盘信号collection名",
        "基金定投实盘信号collection名",
    ]:
        ret_data = {"标识符": data.标识符, "交易日期": data.交易日期, "证券代码": data.证券代码, "交易市场": data.交易市场}
    return ret_data


async def get_strategy_data_list(conn: AsyncIOMotorClient, config: str, filters: dict, sort: list = None):
    future = get_collection_by_config(conn, config).find(filters, sort=sort or [])
    return [row async for row in future]


async def 查询最新策略数据(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, sid: str):
    if strategy_type not in [strategy_type.实盘信号, strategy_type.实盘指标]:
        raise HTTPException(422, detail="错误的策略数据类型")
    col_name = f"{strategy_name}{strategy_type}collection名"
    strategy_info = await get_collection_by_config(conn, f"{strategy_name if strategy_name==策略名称.机器人 else '装备'}信息collection名").find_one({"标识符": sid})
    query_doc = {"标识符": sid}
    class_model = get_strategy_model_by_name(strategy_name, strategy_type)
    if strategy_info["状态"] == 装备状态.已下线:
        query_doc["交易日期"] = get_early_morning(strategy_info["下线时间"])
    else:
        query_doc["交易日期"] = get_early_morning()
        result = await get_collection_by_config(conn, col_name).find_one(query_doc)
        if result:
            return class_model(**result)
        else:
            query_doc["交易日期"] = FastTdate.last_tdate(get_early_morning())
    result = await get_collection_by_config(conn, col_name).find_one(query_doc)
    return class_model(**result) if result else None
