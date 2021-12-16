from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from stralib import get_strategy_signal, FastTdate

from app import settings
from app.crud.base import get_collection_by_config
from app.db.mongodb import db
from app.enums.equipment import 装备分类转换
from app.models.base.equipment import 装备自身运行数据
from app.models.base.robot import 机器人自身运行数据
from app.schedulers import logger
from app.schedulers.base.mongo import mongo_util
from app.schedulers.cn_collection.func import get_client_robot_and_equipment
from app.service.jinniu_data import Beehive
from app.service.datetime import get_early_morning
from app.service.robots.robot import get_robot_and_equipment


def update_operation_data():
    """同步运行数据"""
    logger.info(f"【start】运行数据开始同步")
    robot_list, equipment_list = get_client_robot_and_equipment()
    try:
        update_robot_or_equipment_operation_data(settings.collections.ROBOT, robot_list)
        update_robot_or_equipment_operation_data(settings.collections.EQUIPMENT, equipment_list)
    except Exception as e:
        logger.error(f"运行数据同步出错，错误原因：{e}")
    logger.info(f"【end】运行数据同步完成")


def update_robot_or_equipment_operation_data(table_name: str, sid_list: list) -> None:
    """同步机器人/装备运行数据"""
    logger.info(f"{table_name} 运行数据开始同步")
    data_format_mapping = {settings.collections.EQUIPMENT: 装备自身运行数据, settings.collections.ROBOT: 机器人自身运行数据}[table_name]
    batch_list = []
    for sid in sid_list:
        info = Beehive().query_robot_or_equipment_info(table_name, sid)
        data = data_format_mapping(**info).dict(exclude={"计算时间"})
        batch_list.append(UpdateOne(filter={"标识符": sid}, update={"$set": data}, upsert=True))
    mongo_util.batch_update(table_name=table_name, batch_list=batch_list)
    logger.info(f"{table_name} 运行数据同步结束")


async def update_strategy_calculate_datetime(conn: AsyncIOMotorClient = None, tdate: datetime = None):
    """更新策略计算时间"""
    conn = conn or db.client
    cal_datetime = tdate or get_early_morning()
    cal_datetime = cal_datetime if FastTdate.is_tdate(cal_datetime) else FastTdate.last_tdate(cal_datetime)
    robots, equipments = await get_robot_and_equipment(conn, cal_datetime)
    to_be_update_sid_list = robots + equipments

    async def update_function(collection_name, sid):
        is_updated = await get_collection_by_config(conn, collection_name).find_one({"标识符": sid, "计算时间": cal_datetime})
        if not is_updated:
            await get_collection_by_config(conn, collection_name).update_one({"标识符": sid}, {"$set": {"计算时间": cal_datetime, "updated_at": datetime.now()}})
            to_be_update_sid_list.remove(sid)
            logger.warning(f"{sid} 计算时间更新成功")

    for sid in to_be_update_sid_list[:]:
        col_config_name = f"{'机器人' if sid.startswith('10') else '装备'}信息collection名"
        strategy_type = "机器人" if sid.startswith("10") else 装备分类转换._value2member_map_[sid[:2]].name
        # 当天计算时间更新依据为：sid对应的实盘数据当天是否有益率字段
        if sid.startswith(装备分类转换.选股) or sid.startswith(装备分类转换.择时):
            # 选股装备|择时装备当天实盘信号更新则更新计算时间
            real_signal_number = await get_collection_by_config(conn, f"{strategy_type}实盘信号collection名").count_documents({"标识符": sid, "交易日期": cal_datetime})
            if real_signal_number:
                await update_function(col_config_name, sid)
            else:
                logger.error(f"{sid}-{cal_datetime} 无实盘信号")
        elif sid[:2] in ["10", 装备分类转换.基金定投, 装备分类转换.大类资产配置]:
            # 机器人|大类资产配置|基金定投 当天实盘指标更新则更新计算时间
            real_indicator_number = await get_collection_by_config(conn, f"{strategy_type}实盘指标collection名").count_documents({"标识符": sid, "交易日期": cal_datetime})
            if real_indicator_number:
                await update_function(col_config_name, sid)
            else:
                logger.error(f"{sid}-{cal_datetime} 无实盘信号")
        elif sid[:2] in [装备分类转换.交易, 装备分类转换.风控]:
            # 交易|风控 通过查询adam当天信号更新计算时间
            df = get_strategy_signal(sid, cal_datetime, cal_datetime)
            if not df.empty:
                await update_function(col_config_name, sid)
            else:
                logger.error(f"{sid}-{cal_datetime}-{df} 无实盘信号")
        elif sid[:2].startswith(装备分类转换.风控包):
            # 包 通过查询包中的所有风控装备当天信号更新计算时间
            package_info = await get_collection_by_config(conn, col_config_name).find_one({"标识符": sid})
            if not package_info:
                # 包信息无法查询到，输出日志，并跳过当前循环，防止影响其他策略更新
                logger.error(f"包{sid} 无法查询到信息！请核实是否存在此包！！！")
                continue
            risk_sid_list = package_info.get("装备列表", [])
            update = True
            for risk_sid in risk_sid_list:
                df = get_strategy_signal(risk_sid, cal_datetime, cal_datetime)
                if df.empty:
                    update = False  # 有一个risk_id没有信号，则此风控包不更新
            if update:
                await update_function(col_config_name, sid)
    if to_be_update_sid_list:
        logger.info(f"未更新sid列表为：{to_be_update_sid_list}")
    logger.info(f"【{datetime.now()}】本次更新结束！")
    return to_be_update_sid_list