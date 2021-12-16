import codecs
import csv
import importlib
from copy import deepcopy
from datetime import datetime
from typing import List

import chardet
import pandas as pd
from fastapi import UploadFile, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pandas import DataFrame
from starlette.status import HTTP_405_METHOD_NOT_ALLOWED
from stralib import FastTdate, STRATEGY_SIGNAL_LIBRARY_NAME
from stralib.adam.arctic_store import TimeSeriesStore

from app.core.errors import StrategyDataError, StrategySignalError
from app.crud.base import get_collection_by_config
from app.enums.publish import 错误信息错误类型enum
from app.enums.strategy_data import 策略名称, 策略数据类型
from app.schema.strategy_data import StrategyInCreate, 策略数据InCreate
from app.service.publish.strategy_publish_log import 创建错误日志


def get_strategy_model_by_name(strategy_name: 策略名称, strategy_type: 策略数据类型):
    ip_model = importlib.import_module("app.models.strategy_data")
    return getattr(ip_model, f"{strategy_name}{strategy_type}")


async def 策略数据交易日期连续性检查(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    if hasattr(策略数据[0], "交易日期"):
        # step1: 检查给定数据交易日期是否连续
        tdate_list = sorted([x.交易日期 for x in 策略数据])
        for index, tdate in enumerate(tdate_list[:-1]):
            if FastTdate.next_tdate(tdate) != tdate_list[index + 1]:
                text = f"[{策略数据[0].标识符}]交易日期不连续, 给定数据的交易日期不连续(缺少{tdate}~" f"{tdate_list[index + 1]}的数据)."
                await 创建错误日志(
                    conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, FastTdate.next_tdate(tdate), 错误信息错误类型enum.日期连续性
                )
                raise StrategyDataError(message=text)
        # step2: 检查数据库中最后一个数据是否与给定数据连贯
        recent_tdate_cursor = get_collection_by_config(conn, f"{strategy_name}{strategy_type}collection名").find({"标识符": 策略数据[0].标识符}).sort("交易日期", -1)
        recent_tdate = await recent_tdate_cursor.to_list(length=1)
        if recent_tdate:
            if FastTdate.next_tdate(recent_tdate[0]["交易日期"]) != tdate_list[0]:
                if FastTdate.next_tdate(recent_tdate[0]["交易日期"]) < tdate_list[0]:
                    text = f"[{策略数据[0].标识符}]交易日期不连续, 给定数据与数据库数据的交易日期不连续(" f"缺少{recent_tdate[0]['交易日期']}~{tdate_list[0]})的数据."
                    await 创建错误日志(
                        conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, recent_tdate[0]["交易日期"], 错误信息错误类型enum.日期连续性
                    )
                else:
                    text = f"[{策略数据[0].标识符}]数据重复写入."
                    await 创建错误日志(
                        conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, recent_tdate[0]["交易日期"], 错误信息错误类型enum.重复写入数据
                    )
                raise StrategyDataError(message=text)


async def 策略数据完整性检验_无交易日期(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    if strategy_type == 策略数据类型.回测指标:
        if strategy_name == 策略名称.选股装备:
            await 选股装备回测指标数据完整性检验(conn, strategy_name, strategy_type, 策略数据)
        elif strategy_name == 策略名称.择时装备:
            await 择时装备回测指标数据完整性检验(conn, strategy_name, strategy_type, 策略数据)
    elif strategy_type == 策略数据类型.回测评级:
        if strategy_name == 策略名称.择时装备:
            await 择时装备回测评级数据完整性检验(conn, strategy_name, strategy_type, 策略数据)
        else:
            await 回测评级数据完整性检验(conn, strategy_name, strategy_type, 策略数据)


async def 回测评级数据完整性检验(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    if strategy_type == 策略数据类型.回测评级:
        col_name = f"{strategy_name}{strategy_type}collection名"
        数据集列表 = [x["数据集"] async for x in get_collection_by_config(conn, col_name).find({"标识符": 策略数据[0].标识符})]
        if set(数据集列表) | set([x.数据集 for x in 策略数据]) != {"训练集评级", "测试集评级", "整体评级"}:
            text = f"[{策略数据[0].标识符}]{strategy_type}数据不完整."
            await 创建错误日志(conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, datetime.now(), 错误信息错误类型enum.数据完整性)
            raise StrategyDataError(message=text)


async def 择时装备回测评级数据完整性检验(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    # 择时装备回测评级检查: 和回测评级数据比对开始日期和结束日期
    from app.crud.equipment import 查询某个装备的详情

    equipment_in_db = await 查询某个装备的详情(conn, 策略数据[0].标识符)
    col_name = f"{strategy_name}{strategy_type}collection名"
    总体评级数据_in_db = [x async for x in get_collection_by_config(conn, col_name).find({"标识符": 策略数据[0].标识符, "回测年份": "全部"})]
    if set([x["标的指数"] for x in 总体评级数据_in_db]) | set([x.标的指数 for x in 策略数据 if x.回测年份 == "全部"]) != equipment_in_db.指数列表:
        text = f"[{策略数据[0].标识符}]{strategy_type}数据不完整,缺失标的."
        await 创建错误日志(conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, datetime.now(), 错误信息错误类型enum.数据完整性)
        raise StrategyDataError(message=text)
    年度评级数据_in_db = [x async for x in get_collection_by_config(conn, col_name).find({"标识符": 策略数据[0].标识符, "回测年份": {"$ne": "全部"}})]
    for 标的指数 in equipment_in_db.指数列表:
        标的总体评级数据 = [x for x in 总体评级数据_in_db if x["标的指数"] == 标的指数] or [x for x in 策略数据 if x.标的指数 == 标的指数]
        for i in range(标的总体评级数据[0].开始时间.year, 标的总体评级数据[0].结束时间.year + 1):
            if i not in ([x["回测年份"] for x in 年度评级数据_in_db if x["标的指数"] == 标的指数] + [x.回测年份 for x in 策略数据 if x.回测年份 != "全部" and x.标的指数 == 标的指数]):
                text = f"[{策略数据[0].标识符}]{strategy_type}数据不完整,缺失年度数据."
                await 创建错误日志(conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, datetime.now(), 错误信息错误类型enum.数据完整性)
                raise StrategyDataError(message=text)


async def 选股装备回测指标数据完整性检验(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    # 选股装备回测指标检查: 和回测评级数据比对开始日期和结束日期
    回测评级_col_name = f"{strategy_name}回测评级collection名"
    测试集评级 = await get_collection_by_config(conn, 回测评级_col_name).find_one({"标识符": 策略数据[0].标识符, "数据集": "测试集评级"})
    训练集评级 = await get_collection_by_config(conn, 回测评级_col_name).find_one({"标识符": 策略数据[0].标识符, "数据集": "训练集评级"})
    回测指标数据_in_db = [x async for x in get_collection_by_config(conn, f"{strategy_name}{strategy_type}collection名").find({"标识符": 策略数据[0].标识符})]
    if len({[x["开始时间"], x["结束时间"]] for x in 回测指标数据_in_db} | {[x.开始时间, x.结束时间] for x in 策略数据}) != len(
        {[测试集评级["开始时间"], 测试集评级["结束时间"]], [训练集评级["开始时间"], 训练集评级["结束时间"]]}
    ):
        text = f"[{策略数据[0].标识符}]{strategy_type}数据不完整."
        await 创建错误日志(conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, datetime.now(), 错误信息错误类型enum.数据完整性)
        raise StrategyDataError(message=text)
    if {[x["开始时间"], x["结束时间"]] for x in 回测指标数据_in_db} | {[x.开始时间, x.结束时间] for x in 策略数据} != {[测试集评级["开始时间"], 测试集评级["结束时间"]], [训练集评级["开始时间"], 训练集评级["结束时间"]]}:
        text = f"[{策略数据[0].标识符}]{strategy_type}数据异常."
        await 创建错误日志(conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, datetime.now(), 错误信息错误类型enum.数据完整性)
        raise StrategyDataError(message=text)


async def 择时装备回测指标数据完整性检验(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    # 择时装备回测指标检查: 和回测评级数据比对开始日期和结束日期
    class_model = get_strategy_model_by_name(strategy_name, strategy_type)
    回测评级_in_db = [x async for x in await get_collection_by_config(conn, f"{strategy_name}回测评级collection名").find({"标识符": 策略数据[0].标识符})]
    回测指标_in_db = [x async for x in await get_collection_by_config(conn, f"{strategy_name}{strategy_name}collection名").find({"标识符": 策略数据[0].标识符})]
    if {[x["标的指数"], x["回测年份"]] for x in 回测评级_in_db} != {[x.标的指数, x.回测年份] for x in 策略数据} | set([x["标的指数"], x["回测年份"]] for x in 回测指标_in_db):
        text = f"[{策略数据[0].标识符}]{strategy_type}数据不完整."
        await 创建错误日志(conn, strategy_name, text, f"{strategy_name}{strategy_type}collection名", 策略数据[0].标识符, datetime.now(), 错误信息错误类型enum.数据完整性)
        raise StrategyDataError(message=text)


async def 策略数据完整性检验(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    """
    策略数据完整性检验

    根据是否包含交易日期分成两类，
        包含交易日期则校验
            检查给定数据交易日期是否连续
            检查数据库中最近一个交易日期是否与给定数据连贯
        不包含交易日期
            回测评级：检查数据集是否缺失（训练集评级, 测试集评级, 整体评级）
            择时装备回测评级检查： 根据策略标的指数和全部数据的开始时间和结束时间检查数据完整性
            选股装备回测指标： 根据评级数据比对开始时间和结束时间
            择时装备回测指标： 根据策略指数列表和回测评级数据比对回测年份
    Parameters
    ----------
    conn
    strategy_name
        策略名称
    strategy_type
        策略数据类型
    策略数据

    Returns
    -------

    """
    if hasattr(策略数据[0], "交易日期"):
        await 策略数据交易日期连续性检查(conn, strategy_name, strategy_type, 策略数据)
    else:
        await 策略数据完整性检验_无交易日期(conn, strategy_name, strategy_type, 策略数据)


async def read_strategy_data_from_file(
    file: UploadFile,
):
    """
    从csv文件读取策略数据

    Parameters
    ----------
    file

    Returns
    -------

    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=HTTP_405_METHOD_NOT_ALLOWED)
    code = chardet.detect(await deepcopy(file).read())["encoding"]
    csv_data = csv.DictReader(codecs.iterdecode(file.file, code))
    data = []
    for row in csv_data:
        tmp_dict = {
            "SYMBOL": row["stkcode"],
            "EXCHANGE": row["exchange"],
            "TDATE": datetime.strptime(row["date"], "%Y%m%d"),
            "TCLOSE": row["preclose"],
            "SCORE": 1,
        }
        data.append(tmp_dict)
    return data


async def write_strategy_data_to_adam(sid: str, strategy_data: List[策略数据InCreate], start_date: datetime, end_date: datetime):
    """
    将策略数据写入adam库

    Parameters
    ----------
    sid
    start_date
    end_date
    strategy_data

    Returns
    -------

    """
    data = generate_adam_signal(strategy_data)
    try:
        update_adam_strategy_signal(sid, data, start_date, end_date)
    except Exception as e:
        raise StrategySignalError(message=f"更新策略数据错误，错误信息：{e}")


def generate_adam_signal(strategy_data: List[策略数据InCreate]):
    df = DataFrame([x.dict() for x in strategy_data])
    df = df.set_index(["TDATE"], inplace=False, drop=False)
    df.index.name = "date"
    return df


def generate_empty_adam_signal(tdate: datetime):
    screened_set = pd.DataFrame(data=None, index=[0], columns=["TDATE", "EXCHANGE", "SYMBOL", "TCLOSE", "SCORE"])
    screened_set["TDATE"] = pd.to_datetime(f"{tdate:%Y%m%d}")
    screened_set.set_index(["TDATE"], drop=False, inplace=True)
    screened_set.index.name = "date"
    signals_all = screened_set.astype({"EXCHANGE": str, "SYMBOL": str, "TCLOSE": float, "SCORE": float}, copy=False)
    signals_all = signals_all.apply(lambda x: x.fillna(-1) if x.dtype.kind in "biufc" else x.fillna("."))
    return signals_all


async def update_strategy_online_time(conn: AsyncIOMotorClient, start_date: datetime, sid: str, col_name: str):
    """
    更新策略上线时间

    Parameters
    ----------
    conn
    start_date
    sid
    col_name

    Returns
    -------

    """
    await get_collection_by_config(conn, col_name).update_one({"标识符": sid}, {"$set": {"上线时间": start_date}})


def delete_adam_strategy_signal(strategy_id):
    """
    根据策略id删除adam中相应的信号

    Parameters
    ----------
    strategy_id

    Returns
    -------

    """
    timeseriesstore = TimeSeriesStore(STRATEGY_SIGNAL_LIBRARY_NAME)
    timeseriesstore.delete(strategy_id)


def update_adam_strategy_signal(strategy_id, df, start_datetime, end_datetime):
    """
    根据策略id更新adam中相应的信号

    Parameters
    ----------
    strategy_id
    df
    start_datetime
    end_datetime

    Returns
    -------

    """
    time_series_store = TimeSeriesStore(STRATEGY_SIGNAL_LIBRARY_NAME)
    return time_series_store.update(strategy_id, df, start_datetime, end_datetime)
