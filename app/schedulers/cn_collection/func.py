import logging
from datetime import datetime
from typing import List, Tuple, Dict, Callable

from pymongo import UpdateOne
from stralib import FastTdate

from app import settings
from app.core.errors import ClientHasNoConfig
from app.schedulers.base.mongo import mongo_util
from app.service.jinniu_data import Beehive

ALL_SYNC_COLLECTIONS = ["实盘信号.选股装备", "实盘信号.择时装备", "实盘信号.大类资产配置", "实盘信号.基金定投", "实盘信号.机器人", "实盘指标.机器人", "实盘指标.基金定投", "实盘指标.大类资产配置"]
ALL_BACKTEST_COLLECTIONS = [
    "回测评级.选股装备",
    "回测评级.机器人",
    "回测评级.择时装备",
    "回测评级.大类资产配置",
    "回测评级.基金定投",
    "回测指标.机器人",
    "回测指标.择时装备",
    "回测指标.大类资产配置",
    "回测指标.基金定投",
    "回测信号.选股装备",
    "回测信号.机器人",
    "回测信号.择时装备",
    "回测信号.大类资产配置",
    "回测信号.基金定投",
]


def get_client_robot_and_equipment() -> Tuple[List, List]:
    try:
        user_data = mongo_util.get(table_name=settings.collections.USER, filters={"$or": [{"username": settings.mfrs.CLIENT_USER}, {"mobile": settings.mfrs.CLIENT_USER}]})
        return user_data["client"]["robot"], user_data["client"]["equipment"]
    except KeyError as e:
        raise ClientHasNoConfig(message=f"厂商配置信息获取出错，详情为：{e}")


def format_sids(sid_str: str = None):
    """
    格式化标识符字符串

    多个标识符之间按照符号 "," 区分
    :param sid_str:
    :return:
    """
    robots, equipments = get_client_robot_and_equipment()
    if sid_str:
        robots = [x for x in sid_str.split(",") if x.startswith("10") and x in robots]
        equipments = [x for x in sid_str.split(",") if not x.startswith("10") and x in equipments]
    return robots, equipments


def format_collections(col_str: str = None):
    """
    格式化集合字符串

    多个集合之间按照符号 "," 区分
    :param col_str:
    :return:
    """
    collections = [x for x in col_str.split(",") if x in ALL_SYNC_COLLECTIONS] if col_str else ALL_SYNC_COLLECTIONS
    return collections


def check_local_cn_data_exist(table_name: str, sid_list: list, start: str, end: str):
    """检查本地中文表是否存在数据"""
    current_list = [
        x
        for x in mongo_util.query(
            table_name=table_name,
            filters={"标识符": {"$in": sid_list}, "交易日期": {"$gte": datetime.strptime(start, "%Y-%m-%d"), "$lte": datetime.strptime(end, "%Y-%m-%d")}},
        )
    ]
    if current_list:
        return True
    return False


def get_recent_missing_real_data_date(collection_name: str, sid: str, current_date: datetime = None) -> str:
    """增量情况下，获取最近的缺失数据日期"""
    current_date = current_date or datetime.today()
    while True:
        last_tdate = FastTdate.last_tdate(date=current_date)
        last_data_number = mongo_util.count(table_name=collection_name, filters={"标识符": sid, "交易日期": last_tdate})
        if not last_data_number:  # 上一个交易日数据为空，继续找上上一个交易日
            current_date = last_tdate
        else:
            return current_date.strftime("%Y-%m-%d")


def get_all_missing_real_data_date(collection_name: str, sid: str):
    """获取全部缺失数据的日期"""
    robot_or_equipment_info = mongo_util.get(table_name=settings.collections.ROBOT if collection_name.startswith("机器人", 5) else settings.collections.EQUIPMENT, filters={"标识符": sid})
    online_date = robot_or_equipment_info["上线时间"]
    current_last_tdate = FastTdate.last_tdate(date=datetime.today())
    next_tdate = FastTdate.next_tdate(date=online_date)
    missing_date = []
    while next_tdate <= current_last_tdate:
        data_number = mongo_util.count(table_name=collection_name, filters={"标识符": sid, "交易日期": next_tdate})
        if data_number:  # 数据存在，则继续查找下一个交易日
            next_tdate = FastTdate.next_tdate(date=next_tdate)
        else:
            missing_date.append(next_tdate.strftime("%Y-%m-%d"))
    return missing_date


def get_batch_update_list(table_name: str, params_list: List[Dict[str, str]]):
    """
    获取批量更新数据列表
    Parameters
    ----------
    table_name
    params_list [{"sid","start","end"}]

    Returns
    -------

    """
    query_list = Beehive().query_cn_data(table_name, params_list)
    batch_list = []
    for data in query_list:
        data["交易日期"] = datetime.strptime(data["交易日期"], "%Y-%m-%dT%H:%M:%SZ")
        filters = {"交易日期": data["交易日期"], "标识符": data["标识符"]}
        if "标的指数" in data.keys():
            filters["标的指数"] = data["标的指数"]
        if "证券代码" in data.keys():
            filters["证券代码"] = data["证券代码"]
        batch_list.append(UpdateOne(filter=filters, update={"$set": data}, upsert=True))
    return batch_list


def update_real_collection_data(col_str: str = None, sid_str: str = None, params_func: Callable = None):
    """同步实盘表数据"""
    robots, equipments = format_sids(sid_str)
    collections = format_collections(col_str)
    sid_list = robots + equipments
    for col_name in collections:
        filtered_sid_list = Beehive().filter_sid(col_name, sid_list)
        params_list = params_func(col_name, filtered_sid_list)
        batch_list = get_batch_update_list(col_name, params_list)
        if not batch_list:
            # 查询无数据，提示异常
            logging.warning(f"【{col_name} 数据源为空，查询条件为{params_list}】")
            continue
        try:
            mongo_util.batch_update(table_name=col_name, batch_list=batch_list)
        except Exception as e:
            logging.error(f"同步错误，详情：{e}")
            break


def increment_update_cn_collection_data():
    """增量更新实盘数据"""
    current_date = datetime.now()
    end_date = current_date.strftime("%Y-%m-%d")
    increment_update_params_func = lambda col_name, sid_list: [
        {"sid": sid, "start": get_recent_missing_real_data_date(col_name, sid, current_date), "end": end_date} for sid in sid_list
    ]
    update_real_collection_data(params_func=increment_update_params_func)


def added_missing_real_collection_data():
    """补充实盘缺失数据"""
    added_missing_params_func = lambda col_name, sid_list: [
        {"sid": sid, "start": tdate, "end": tdate} for sid in sid_list for tdate in get_all_missing_real_data_date(col_name, sid)
    ]
    update_real_collection_data(params_func=added_missing_params_func)


def full_quantity_update_real_data(start: str = None, end: str = None, col_str: str = None, sid_str: str = None):
    """按指定条件全量更新实盘数据"""
    if not all([start, end]):
        start = end = datetime.now().strftime("%Y-%m-%d")
    full_quantity_func = lambda col_name, sid_list: [{"sid": sid, "start": start, "end": end} for sid in sid_list]
    update_real_collection_data(col_str=col_str, sid_str=sid_str, params_func=full_quantity_func)


def get_backtest_batch_update_list(table_name: str, sid_list: list, params: dict = None):
    """获取回测数据批量更新列表"""
    query_list = Beehive().query_backtest_data(table_name, sid_list, params)
    batch_list = []
    for data in query_list:
        filters = {"标识符": data["标识符"]}
        if "交易日期" in data.keys():
            filters["交易日期"] = data["交易日期"]
        if "标的指数" in data.keys():
            filters["标的指数"] = data["标的指数"]
        if "证券代码" in data.keys():
            filters["证券代码"] = data["证券代码"]
        if "数据集" in data.keys():
            filters["数据集"] = data["数据集"]
        if "回测年份" in data.keys():
            filters["回测年份"] = data["回测年份"]
        batch_list.append(UpdateOne(filter=filters, update={"$set": data}, upsert=True))
    return batch_list


def update_backtest_collection_data(start: str = None, end: str = None, col_str: str = None, sid_str: str = None):
    """同步回测数据，支持覆盖更新"""
    if not all([start, end]):
        start = end = datetime.now().strftime("%Y-%m-%d")
    robots, equipments = format_sids(sid_str)
    backtest_collections = [x for x in col_str.split(",") if x in ALL_BACKTEST_COLLECTIONS] if col_str else ALL_BACKTEST_COLLECTIONS
    for col_name in backtest_collections:
        sid_list = robots if col_name.endswith("机器人") else equipments
        batch_list = get_backtest_batch_update_list(col_name, sid_list, params={"start": start, "end": end, "limit": 10000})
        if not batch_list:
            logging.warning(f"{start}-{end}：【无数据】")
            continue
        try:
            mongo_util.batch_update(table_name=col_name, batch_list=batch_list)
        except Exception as e:
            logging.error(f"同步错误，详情：{e}")
            break


def del_cn_collection(start: str = None, end: str = None, collection: str = None, sid_list: str = None):
    """删除中文表记录"""
    if not all([start, end]):
        start = end = datetime.now()
    else:
        start = datetime.strptime(start, "%Y-%m-%d")
        end = datetime.strptime(end, "%Y-%m-%d")
    robots, equipments = format_sids(sid_list)
    collections = (
        [x for x in collection.split(",") if x in ALL_BACKTEST_COLLECTIONS + ALL_SYNC_COLLECTIONS]
        if collection
        else ALL_BACKTEST_COLLECTIONS + ALL_SYNC_COLLECTIONS
    )
    for col_name in collections:
        sid_list = robots if col_name.endswith("机器人") else equipments
        for sid in sid_list:
            if collection in ALL_SYNC_COLLECTIONS:
                filters = {"交易日期": {"gte": start, "lte": end}, "标识符": sid}
            else:
                filters = {"标识符": sid}
            try:
                mongo_util.delete(collection, filters=filters)
            except Exception as e:
                logging.error(f"删除失败，详情：{e}")
