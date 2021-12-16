from copy import copy
from datetime import datetime, timedelta
from typing import List

import pytest
from stralib import FastTdate

from app.enums.fund_account import FlowTType
from app.models.fund_account import FundAccountFlowInDB, FundAccountInDB
from app.models.rwmodel import PyObjectId
from app.models.time_series_data import (
    FundTimeSeriesDataInDB,
    PositionTimeSeriesDataInDB,
)
from app.schema.fund_account import FundAccountFlowInCreate
from app.service.fund_account.fund_account import calculate_flow_fee
from app.utils.datetime import date2datetime


@pytest.fixture
def fund_account_data():
    data = {
        "_id": str(PyObjectId()),
        "capital": "1000000.0",
        "assets": "1000000",
        "cash": "1000000",
        "securities": "0.00",
        "commission": "0.0003",
        "tax_rate": "0.001",
        "slippage": "0.01",
        "ts_data_sync_date": date2datetime(),
    }
    return data


@pytest.fixture
def fund_account_flow_data():
    data = {
        "fund_id": "60122d282c27e2a494940a36",
        "symbol": "600519",
        "exchange": "CNSESH",
        "stkeffect": "10000",
        "tdate": str(datetime.today().date()),
        "cost": 10,
    }
    return data


@pytest.fixture
def fund_account_position_data():
    data = {
        "fund_id": "6062915edd2fd56eaa510a9b",
        "symbol": "603386",
        "exchange": "CNSESH",
        "volume": 60000,
        "cost": "0.01",
        "first_buy_date": "2021-03-30T03:16:07.653+0000",
        "id": "606297f75d7a63a9951e5fca",
    }
    return data


@pytest.fixture
def fund_account_flow_in_db(fund_account_flow_data):
    return FundAccountFlowInDB(**fund_account_flow_data, ttype="3")


@pytest.fixture
def fund_account_flow_list(
    fixture_db, fund_account_data, fund_account_flow_data
) -> List[FundAccountFlowInDB]:
    fund_account = FundAccountInDB(**fund_account_data)
    # 计算流水数据时需要资金账户的佣金税费等数据

    tdate = date2datetime()
    # 获取前4个交易日, 从最早的交易日开始排列
    # day1为流水同步日
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )
    fund_account_flow_list = []
    # day2 以每股10元成本价买入10000股600519
    day2_flow_data = copy(fund_account_flow_data)
    day2_flow_data["tdate"] = day2.date()
    day2_flow_data["ttype"] = FlowTType.BUY
    day2_flow = calculate_flow_fee(
        fund_account, FundAccountFlowInCreate(**day2_flow_data)
    )
    fund_account_flow_list.append(day2_flow)
    # day3 以每股10元卖出5000股600519
    day3_flow_data = copy(fund_account_flow_data)
    day3_flow_data["tdate"] = day3.date()
    day3_flow_data["ttype"] = FlowTType.SELL
    day3_flow_data["stkeffect"] = "-5000"
    day3_flow_data["cost"] = "10"
    day3_flow = calculate_flow_fee(
        fund_account, FundAccountFlowInCreate(**day3_flow_data)
    )
    fund_account_flow_list.append(day3_flow)
    # day4 以每股10元成本价买入1000股600519
    day4_flow_data = copy(fund_account_flow_data)
    day4_flow_data["tdate"] = day4.date()
    day4_flow_data["ttype"] = FlowTType.BUY
    day4_flow_data["stkeffect"] = "1000"
    day4_flow_data["cost"] = "10"
    day4_flow = calculate_flow_fee(
        fund_account, FundAccountFlowInCreate(**day4_flow_data)
    )
    fund_account_flow_list.append(day4_flow)
    return fund_account_flow_list


@pytest.fixture
def fund_time_series_data():
    data = {
        "fund_id": "60122d282c27e2a494940a36",
        "tdate": date2datetime(),
        "fundbal": "1000000",
        "mktval": "0",
    }
    return data


@pytest.fixture
def fund_time_series_data_list(fund_time_series_data) -> List[FundTimeSeriesDataInDB]:
    """资金账户资产时点数据, 对应上方流水."""
    tdate = date2datetime()
    # 获取过去4个交易日
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )
    fund_time_series_in_db_list = []
    day1_time_series_data = copy(fund_time_series_data)
    day1_time_series_data["tdate"] = day1
    fund_time_series_in_db_list.append(FundTimeSeriesDataInDB(**day1_time_series_data))
    day2_time_series_data = copy(fund_time_series_data)
    day2_time_series_data["tdate"] = day2
    day2_time_series_data["fundbal"] = "900000"
    day2_time_series_data["mktval"] = "100000"
    fund_time_series_in_db_list.append(FundTimeSeriesDataInDB(**day2_time_series_data))
    day3_time_series_data = copy(fund_time_series_data)
    day3_time_series_data["tdate"] = day3
    day3_time_series_data["fundbal"] = "950000"
    day3_time_series_data["mktval"] = "50000"
    fund_time_series_in_db_list.append(FundTimeSeriesDataInDB(**day3_time_series_data))
    day4_time_series_data = copy(fund_time_series_data)
    day4_time_series_data["tdate"] = day4
    day4_time_series_data["fundbal"] = "940000"
    day4_time_series_data["mktval"] = "60000"
    fund_time_series_in_db_list.append(FundTimeSeriesDataInDB(**day4_time_series_data))
    return fund_time_series_in_db_list


@pytest.fixture
def position_time_series_data():
    data = {
        "fund_id": "60122d282c27e2a494940a36",
        "tdate": date2datetime(),
        "position_list": [],
    }
    return data


@pytest.fixture
def position_time_series_data_list(
    position_time_series_data,
) -> List[PositionTimeSeriesDataInDB]:
    """资金账户持仓时点数据, 对应上方流水."""
    tdate = date2datetime()
    # 获取过去4个交易日
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )
    position_time_series_data_in_db_list = []
    day1_position_time_series_data = copy(position_time_series_data)
    day1_position_time_series_data["tdate"] = day1
    position_time_series_data_in_db_list.append(
        PositionTimeSeriesDataInDB(**day1_position_time_series_data)
    )
    day2_position_time_series_data = copy(position_time_series_data)
    day2_position_time_series_data["tdate"] = day2
    day2_position_time_series_data["position_list"] = [
        {
            "symbol": "600519",
            "market": "CNSESH",
            "stkbal": 10000,
            "mktval": "100000",
            "buy_date": day2,
        }
    ]
    position_time_series_data_in_db_list.append(
        PositionTimeSeriesDataInDB(**day2_position_time_series_data)
    )
    day3_position_time_series_data = copy(position_time_series_data)
    day3_position_time_series_data["tdate"] = day3
    day3_position_time_series_data["position_list"] = [
        {
            "symbol": "600519",
            "market": "CNSESH",
            "stkbal": 5000,
            "mktval": "50000",
            "buy_date": day2,
        }
    ]
    position_time_series_data_in_db_list.append(
        PositionTimeSeriesDataInDB(**day3_position_time_series_data)
    )
    day4_position_time_series_data = copy(position_time_series_data)
    day4_position_time_series_data["tdate"] = day4
    day4_position_time_series_data["position_list"] = [
        {
            "symbol": "600519",
            "market": "CNSESH",
            "stkbal": 6000,
            "mktval": "60000",
            "buy_date": day2,
        }
    ]
    position_time_series_data_in_db_list.append(
        PositionTimeSeriesDataInDB(**day4_position_time_series_data)
    )
    return position_time_series_data_in_db_list
