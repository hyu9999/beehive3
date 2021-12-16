from datetime import datetime

import pandas as pd
from pandas import DataFrame

from app.enums.equipment import 装备分类转换
from tests.consts.signal import const_signal


def mock_empty_dataframe(*args):
    return DataFrame()


def mock_get_strategy_signal(strategy_id, start_datetime, end_datetime) -> DataFrame:
    equipment_type = 装备分类转换.__dict__["_value2member_map_"][strategy_id[:2]].name
    return DataFrame(
        const_signal[equipment_type]["data"],
        const_signal[equipment_type]["idx"],
    )


def mock_get_strategy_flow(strategy_id, start_datetime, end_datetime) -> DataFrame:
    """随机选取数据库中已上线的机器人，mock 机器人策略信号"""
    data = [
        {"tdate": "2020-11-26 00:00:00", "exchange": "CNSESZ", "symbol": "002030", "signal": 1.00000, "operator": 12.00000, "tradenum": 100.0, "tprice": 33.43}
    ]
    idx = ["2020-11-26T00:00:00"]
    df1 = pd.DataFrame(data, index=idx)
    return df1


async def mock_check_equip_status_success(*args):
    return True


async def mock_check_equip_status_failed(*args):
    return False


async def mock_update_stralib_robot_data(sid: str, tdate: datetime):
    pass


async def mock_获取选股信号列表(*args):
    data = {
        "TDATE": [pd.Timestamp("2020-11-30"), pd.Timestamp("2020-11-30")],
        "EXCHANGE": ["0", "0"],
        "SYMBOL": ["002030", "002932"],
        "TCLOSE": [32.96, 61.16],
        "SYMBOL_NAME": ["达安基因", "明德生物"],
        "REALTIME_PRICE": [36.51, 83.85],
    }
    return DataFrame(data)


async def mock_获取择时信号列表(*args):
    data = {
        "市场趋势形态": ["反弹", "反弹"],
        "建议仓位": ["30-50%", "70-100%"],
        "理想仓位": [0.50, 0.60],
        "指数": ["深证成指", "深证成指"],
        "信号日期": [pd.Timestamp("2020-11-30"), pd.Timestamp("2020-12-01")],
    }
    idx = pd.Index([pd.Timestamp("2020-11-30"), pd.Timestamp("2020-12-01")])
    return DataFrame(data, idx)


async def mock_获取大类资产配置信号列表(*args):
    data = {
        "时间": [pd.Timestamp("2020-11-30"), pd.Timestamp("2020-12-01")],
        "股票名称": ["达安基因", "明德生物"],
        "股票代码": ["002030", "002932"],
        "操作": ["0", "0"],
        "股数": [100, 200],
        "仓位": [0.50, 0.60],
    }
    return DataFrame(data)


async def mock_get_equipment_signal(*args):
    return DataFrame(
        {"时间": [pd.Timestamp("2020-11-05")], "股票名称": ["华安易富黄金ETF"], "股票代码": ["518880"], "操作": ["卖出"], "股数": [-100], "价格(元)": [3.94981], "仓位": ["3.9%"]}
    )
