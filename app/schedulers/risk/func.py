import asyncio
import pickle
from datetime import datetime
from math import ceil
from typing import List

from pymongo import ASCENDING
from stralib import FastTdate

from app.crud.base import get_robots_collection
from app.db.mongodb import db
from app.global_var import G
from app.outer_sys.stralib.robot.run_robot import robot_source_data
from app.schedulers import logger
from app.service.check_status import CheckStatus
from app.service.datetime import get_early_morning
from app.service.risks.detection import risk_detection_by_robot


async def risk_detection_with_condition_task():
    """
    风险检测任务: 带条件

    Returns
    -------

    """
    logger.info("【start】风险检测")
    start_date = datetime.now().date()
    robot_queryset = get_robots_collection(db.client).find({"状态": {"$in": ["已上线", "已下线"]}})
    all_robot = [x["标识符"] async for x in robot_queryset]
    executed_robot = []  # 已经执行完的机器人
    计算时间 = get_early_morning()
    while True:
        logger.info(f"循环检测 开始")
        if all_robot == executed_robot:
            logger.info("全部执行完毕！")
            break
        date = datetime.now().date()
        if start_date != date:
            logger.info("当日零点自动结束检测！")
            break
        try:
            account_status = await CheckStatus.check_time_series_status()
        except Exception as e:
            logger.error(f"【同步流水状态】 失败 {e}")
            break
        logger.info(f"【同步流水状态】{account_status}")
        execute_robot_queryset = get_robots_collection(db.client).find(
            {
                "状态": {"$in": ["已上线", "已下线"]},
                "计算时间": 计算时间,
                "标识符": {"$nin": executed_robot},
            }
        )
        execute_robot = [x["标识符"] async for x in execute_robot_queryset]
        executed_robot.extend(execute_robot)
        if account_status:
            await risk_detection_by_robot(db.client, execute_robot, send_msg=False)
            break
        else:
            logger.warning("【risk_detection】数据未准备完毕，等待")
            await asyncio.sleep(300)
    logger.info(f"【end】风险检测")


async def risk_detection_task():
    """
    风险检测任务

    Returns
    -------

    """
    logger.info("【start】风险检测")
    await risk_detection_by_robot(db.client, send_msg=False)
    logger.info(f"【end】风险检测")


async def preload_robot_data(job_idx: int, job_num: int, robot_sid_list: List[str] = None):
    """提前加载robot_data，未加载则表明该robot计算时间未正常更新"""
    logger.info(f"【start】加载robot_data {job_idx}")
    db_query = {"状态": {"$in": ["已上线", "已下线"]}}
    if robot_sid_list:
        db_query["标识符"] = {"$in": robot_sid_list}
    robot_queryset_num = await get_robots_collection(db.client).count_documents(db_query)
    limit = ceil(robot_queryset_num / job_num)
    robot_queryset = get_robots_collection(db.client).find(db_query).sort([("标识符", ASCENDING)]).skip(job_idx * limit).limit(limit)
    pipeline = await G.preload_redis.pipeline()
    async for dbrobot in robot_queryset:
        # 缓存计算时间是上一个交易日的robot_data数据，为保证任何时间点能获取到数据，定时任务执行开始时间为0点，周期是每天
        if dbrobot["计算时间"] == FastTdate.last_tdate(get_early_morning(datetime.now())):
            robot_data = await robot_source_data(dbrobot, dbrobot["计算时间"], dbrobot["计算时间"])
            robot_data_bytes = pickle.dumps(robot_data)
            pipeline.set(
                f"stralib_robot_data_{dbrobot['标识符']}",
                robot_data_bytes,
                expire=3600 * 24,
            )
    await pipeline.execute()
    logger.info(f"【end】加载robot_data {job_idx}")
