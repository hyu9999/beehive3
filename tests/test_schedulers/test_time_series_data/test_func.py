from datetime import timedelta
from decimal import Decimal

import pytest
from stralib import FastTdate

from app.enums.fund_account import CurrencyType
from app.enums.portfolio import PortfolioCategory
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.schedulers.time_series_data.func import (
    generate_history_time_series_data,
    save_history_time_series_data,
    save_today_time_series_data,
)
from app.utils.datetime import date2datetime
from tests.test_helper import get_random_str

pytestmark = pytest.mark.asyncio


async def test_save_today_time_series_data(mocker, fund_account_data):
    class FakeData:
        @staticmethod
        def dict(*args, **kwargs):
            ...

    async def coro(*args, **kwargs):
        return FakeData

    mocker.patch(
        "app.schedulers.time_series_data.func.position2time_series", side_effect=coro
    )
    mocker.patch(
        "app.schedulers.time_series_data.func.fund2time_series", return_value=FakeData
    )
    mocker.patch(
        "app.schedulers.time_series_data.func.get_fund_account_position",
        side_effect=coro,
    )
    fund_account_in_db = FundAccountInDB(**fund_account_data)
    operations = await save_today_time_series_data(
        fund_account_in_db, date2datetime(), PortfolioCategory.ManualImport
    )
    assert len(operations) == 2


async def test_generate_history_time_series_data(
    fund_account_data, fund_account_flow_data, mocker, fund_account_flow_list
):
    # 获取4个交易日, 从最早的交易日开始排列
    # day1为流水同步日
    tdate = date2datetime()
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )

    # 设置资金账户资产, 流水同步日期为4个交易日前
    fund_account = FundAccountInDB(**fund_account_data)
    fund_account.ts_data_sync_date = day1
    fund_id = str(fund_account.id)

    # 设置资金账户当前持仓
    fund_account_position = [
        FundAccountPositionInDB(
            fund_id=fund_id,
            symbol=fund_account_flow_data["symbol"],
            exchange=fund_account_flow_data["exchange"],
            volume=6000,
            cost=10,
            first_buy_date=day2,
        )
    ]

    # 设置资金账户当前资产
    fund_account.securities = Decimal(60000)
    fund_account.cash = fund_account.cash.to_decimal() - fund_account.securities

    async def fake_get_fund_account_flow(*args, **kwargs):
        return fund_account_flow_list

    async def fake_get_fund_account_position(*args, **kwargs):
        return fund_account_position

    async def fake_get_security_price(*args, **kwargs):
        class FakeSecurityPrice:
            current = Decimal(10)

        return FakeSecurityPrice()

    mocker.patch(
        "app.schedulers.time_series_data.func.get_fund_account_flow",
        side_effect=fake_get_fund_account_flow,
    )
    mocker.patch(
        "app.schedulers.time_series_data.func.get_fund_account_position",
        side_effect=fake_get_fund_account_position,
    )
    mocker.patch(
        "app.service.time_series_data.converter.get_security_price",
        side_effect=fake_get_security_price,
    )
    (
        position_time_series_list,
        fund_time_series_list,
    ) = await generate_history_time_series_data(
        fund_account,
        day2,
        day4,
        category=PortfolioCategory.ManualImport,
        currency=CurrencyType.CNY,
    )
    # 是否包含4个交易日的数据
    assert len(position_time_series_list) == 4
    assert len(fund_time_series_list) == 4
    # 是否为day1~day4这4个交易日
    for day in [day1, day2, day3, day4]:
        assert day in [i.tdate for i in position_time_series_list]
        assert day in [i.tdate for i in fund_time_series_list]
    # 持仓时点数据是否计算正确
    expect_position_line = [None, 10000, 5000, 6000]
    position_line = [
        position.position_list[0].stkbal if getattr(position, "position_list") else None
        for position in sorted(position_time_series_list, key=lambda p: p.tdate)
    ]
    assert expect_position_line == position_line
    # 资产时点数据是否计算正确
    expect_fund_line = [1000000, 900000, 950000, 940000]
    fund_line = [
        float(fund.fundbal.to_decimal())
        for fund in sorted(fund_time_series_list, key=lambda f: f.tdate)
    ]
    assert expect_fund_line == fund_line


async def test_save_history_time_series_data(mocker, fund_account_data):
    class FakeData:
        tdate = date2datetime()
        fund_id = get_random_str()

        @staticmethod
        def dict(*args, **kwargs):
            ...

    async def coro(*args, **kwargs):
        return [FakeData], [FakeData]

    mocker.patch(
        "app.schedulers.time_series_data.func.generate_history_time_series_data",
        side_effect=coro,
    )
    fund_account_in_db = FundAccountInDB(**fund_account_data)
    tdate = date2datetime()
    operations = await save_history_time_series_data(
        fund_account_in_db,
        tdate,
        tdate,
        PortfolioCategory.ManualImport,
        CurrencyType.CNY,
    )
    assert len(operations) == 2
