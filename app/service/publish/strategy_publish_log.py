from collections import defaultdict
from datetime import datetime
from typing import Union, List

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app.crud.base import get_collection_by_config
from app.schema.equipment import (
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
    基金定投实盘指标InCreate,
    基金定投实盘信号InCreate
)
from app.crud.publish import get_strategy_daily_log, replace_strategy_daily_log_by_id, \
    update_strategy_daily_error_log_by_id
from app.crud.publish import create_strategy_daily_log as create_strategy_daily_log_crud
from app.enums.publish import 发布情况enum, 错误信息数据类型enum, 策略分类enum, 错误信息错误类型enum, 错误触发源enum
from app.models.base.publish import StrategyErrorLogDetail
from app.schema.publish import StrategyDailyLogInCreate
from app.schema.robot import 机器人实盘指标InCreate, 机器人实盘信号InCreate, 机器人回测评级InCreate, 机器人回测信号InCreate, 机器人回测指标InCreate


async def create_strategy_daily_log(
    conn: AsyncIOMotorClient,
    strategy_daily_log: StrategyDailyLogInCreate,
):
    """创建每日策略日志.
        每日每条策略只存在一条记录。
        对于错误日志：先查找是否存在当天的日志，若已存在且日志类型为错误日志，则追加错误信息到该记录。若已存在且日志类型为成功日志，则替换该记录
        对于成功日志：先查找是否存在当天的日志，若存在则替换该记录。若不存在则创建新记录。
    """
    log = await get_strategy_daily_log(conn, strategy_daily_log.分类, strategy_daily_log.标识符, strategy_daily_log.交易日期)
    if not log:
        await create_strategy_daily_log_crud(conn, strategy_daily_log)
    else:
        if log.发布情况 == 发布情况enum.failed and strategy_daily_log.发布情况 == 发布情况enum.failed:
            await update_strategy_daily_error_log_by_id(conn, log.id, strategy_daily_log)
        else:
            await replace_strategy_daily_log_by_id(conn, log.id, strategy_daily_log)


def 查询错误数据类型(collection_name: str):
    if "信号" in collection_name:
        return 错误信息数据类型enum.信号
    elif "指标" in collection_name:
        return 错误信息数据类型enum.指标
    elif "评级" in collection_name:
        return 错误信息数据类型enum.评级


def 查询触发源(collection_name: str):
    if "实盘" in collection_name:
        return 错误触发源enum.实盘
    elif "回测" in collection_name:
        return 错误触发源enum.回测


def 查询策略分类(collection_name: str):
    if "选股" in collection_name:
        return 策略分类enum.选股
    elif "择时" in collection_name:
        return 策略分类enum.择时
    elif "交易" in collection_name:
        return 策略分类enum.交易
    elif "风控" in collection_name:
        return 策略分类enum.风控
    elif "基金定投" in collection_name:
        return 策略分类enum.基金定投
    elif "大类资产配置" in collection_name:
        return 策略分类enum.大类资产配置


async def 创建错误日志(
    conn: AsyncIOMotorClient,
    category: 策略分类enum,
    text: str,
    collection_name: str,
    sid: str,
    tdate: datetime,
    错误类型: 错误信息错误类型enum,
):
    strategy_error_log_detail = StrategyErrorLogDetail(
        触发源=查询触发源(collection_name),
        数据类型=查询错误数据类型(collection_name),
        错误类型=错误类型,
        详情=text
    )
    strategy_daily_log = StrategyDailyLogInCreate(
        分类=category,
        标识符=sid,
        交易日期=tdate,
        发布情况=发布情况enum.failed,
        错误信息=[strategy_error_log_detail]
    )
    await create_strategy_daily_log(conn, strategy_daily_log)


async def 创建成功日志(
    conn: AsyncIOMotorClient,
    category: 策略分类enum,
    sid: str,
    tdate: datetime,
) -> None:
    strategy_daily_log = StrategyDailyLogInCreate(
        分类=category,
        标识符=sid,
        交易日期=tdate,
        发布情况=发布情况enum.success,
        错误信息=[]
    )
    await create_strategy_daily_log(conn, strategy_daily_log)


async def 实盘回测数据交易日期连续性检查(
    conn: AsyncIOMotorClient,
    collectionName: str,
    category: 策略分类enum,
    实盘回测数据: List[
        Union[
            机器人回测指标InCreate,
            机器人回测信号InCreate,
            机器人回测评级InCreate,
            机器人实盘信号InCreate,
            机器人实盘指标InCreate,
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
):
    # 没有`收益率`字段的数据 或 无`交易日期`字段，无法进行交易日连续性检查
    if hasattr(实盘回测数据[0], "收益率") or hasattr(实盘回测数据[0], "交易日期"):
        d = defaultdict(list)
        for obj in 实盘回测数据:
            d[obj.交易日期].append(obj)
        tdate_list = list(d.keys())
        tdate_list.sort()
        # step1: 检查给定数据交易日期是否连续
        for index, tdate in enumerate(tdate_list[:-1]):
            if FastTdate.next_tdate(tdate) != tdate_list[index + 1]:
                text = f"[{实盘回测数据[0].标识符}]交易日期不连续, 给定数据的交易日期不连续(缺少{tdate}~" \
                       f"{tdate_list[index + 1]}的数据)."
                await 创建错误日志(conn, category, text, collectionName, 实盘回测数据[0].标识符, FastTdate.next_tdate(tdate),
                             错误信息错误类型enum.日期连续性)
                raise HTTPException(400, detail=text)
        # step2: 检查数据库中最后一个数据是否与给定数据连贯
        recent_tdate_cursor = get_collection_by_config(conn, collectionName).find({"标识符": 实盘回测数据[0].标识符}).sort("交易日期", -1)
        recent_tdate = await recent_tdate_cursor.to_list(length=1)
        if recent_tdate:
            if FastTdate.next_tdate(recent_tdate[0]["交易日期"]) != tdate_list[0]:
                if FastTdate.next_tdate(recent_tdate[0]["交易日期"]) < tdate_list[0]:
                    text = f"[{实盘回测数据[0].标识符}]交易日期不连续, 给定数据与数据库数据的交易日期不连续(" \
                           f"缺少{recent_tdate[0]['交易日期']}~{tdate_list[0]})的数据."
                    await 创建错误日志(conn, category, text, collectionName, 实盘回测数据[0].标识符, recent_tdate[0]["交易日期"],
                                 错误信息错误类型enum.日期连续性)
                else:
                    text = f"[{实盘回测数据[0].标识符}]数据重复写入."
                    await 创建错误日志(conn, category, text, collectionName, 实盘回测数据[0].标识符, recent_tdate[0]["交易日期"],
                                 错误信息错误类型enum.重复写入数据)
                raise HTTPException(400, detail=text)
