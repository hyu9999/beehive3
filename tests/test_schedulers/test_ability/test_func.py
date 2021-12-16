import datetime

import pytest
from pytest import mark
from stralib import FastTdate

from app.enums.portfolio import PortfolioCategory
from app.models.base.portfolio import 用户资金账户信息
from app.models.rwmodel import PyObjectId
from app.schedulers.ability.func import (
    calculate_portfolio_ability,
    create_portfolio_assessment_time_series_data,
    get_ability_assets,
    get_ability_flows,
    get_ability_stocks,
    get_stock_stats,
    get_tdate_by_stage,
    update_portfolio_analysis,
    update_portfolio_stage_profit,
)
from app.schema.portfolio import PortfolioInResponse
from app.utils.datetime import date2datetime

pytestmark = pytest.mark.asyncio


async def test_update_portfolio_analysis(fixture_db, portfolio_data_in_db):
    portfolio_in_response = PortfolioInResponse(**portfolio_data_in_db)
    operations = await update_portfolio_analysis(portfolio_in_response, date2datetime())
    assert operations


@pytest.fixture
async def test_get_ability_flows(
    mocker,
    fund_account_flow_list,
):
    start_date = date2datetime()
    end_date = date2datetime()
    fund_id_list = [用户资金账户信息()]

    async def coro(*args, **kwargs):
        return fund_account_flow_list

    get_flow = mocker.patch(
        "app.schedulers.ability.func.get_fund_account_flow", side_effect=coro
    )
    ability_flows = await get_ability_flows(
        start_date, end_date, fund_id_list, PortfolioCategory.ManualImport
    )
    assert get_flow.called
    assert len(ability_flows.df.to_dict("records")) == len(fund_account_flow_list)
    return ability_flows


@pytest.fixture
async def test_get_ability_assets(
    mocker,
    fund_time_series_data_list,
):
    start_date = date2datetime()
    end_date = date2datetime()
    fund_id_list = ["1"]

    async def coro(*args, **kwargs):
        return fund_time_series_data_list

    get_fund = mocker.patch(
        "app.schedulers.ability.func.get_fund_time_series_data", side_effect=coro
    )
    ability_assets = await get_ability_assets(start_date, end_date, fund_id_list)
    assert get_fund.called
    assert len(ability_assets.df.to_dict("records")) == len(fund_time_series_data_list)
    return ability_assets


@pytest.fixture
async def test_get_ability_stocks(mocker, position_time_series_data_list):
    start_date = date2datetime()
    end_date = date2datetime()
    fund_id_list = ["1"]

    async def coro(*args, **kwargs):
        return position_time_series_data_list

    get_position = mocker.patch(
        "app.schedulers.ability.func.get_position_time_series_data", side_effect=coro
    )
    ability_stocks = await get_ability_stocks(start_date, end_date, fund_id_list)
    assert get_position.called
    # 由于去掉了我持仓的交易日，所以要加1
    assert len(ability_stocks.df.to_dict("records")) + 1 == len(
        position_time_series_data_list
    )
    return ability_stocks


@pytest.fixture
async def test_calculate_portfolio_ability(
    mocker,
    test_get_ability_flows,
    test_get_ability_assets,
    test_get_ability_stocks,
    portfolio_data_in_db,
):
    mocker.patch("app.schedulers.ability.func.FastTdate.is_tdate", return_value=True)
    tdate = date2datetime()
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(
        tdate - datetime.timedelta(days=100), tdate
    )

    async def fake_ability_flows(*args, **kwargs):
        return test_get_ability_flows

    async def fake_ability_assets(*args, **kwargs):
        return test_get_ability_assets

    async def fake_ability_stocks(*args, **kwargs):
        return test_get_ability_stocks

    mocker.patch(
        "app.schedulers.ability.func.get_ability_flows", side_effect=fake_ability_flows
    )
    mocker.patch(
        "app.schedulers.ability.func.get_ability_assets",
        side_effect=fake_ability_assets,
    )
    mocker.patch(
        "app.schedulers.ability.func.get_ability_stocks",
        side_effect=fake_ability_stocks,
    )

    portfolio_in_response = PortfolioInResponse(**portfolio_data_in_db)

    # 验证计算过程无报错即可
    return await calculate_portfolio_ability(portfolio_in_response, day1, day4)


@mark.skip
async def test_update_portfolio_stage_profit(test_calculate_portfolio_ability):
    await update_portfolio_stage_profit(test_calculate_portfolio_ability, PyObjectId())


@mark.skip
async def test_create_portfolio_assessment_time_series_data(
    test_calculate_portfolio_ability,
):
    operations = await create_portfolio_assessment_time_series_data(
        PyObjectId(), test_calculate_portfolio_ability
    )
    assert operations[0]


def test_get_tdate_by_stage():
    for stage in [
        "last_tdate",
        "last_week",
        "last_month",
        "last_3_month",
        "last_half_year",
        "last_year",
    ]:
        get_tdate_by_stage(date2datetime(), stage)


async def test_get_stock_stats(test_calculate_portfolio_ability, mocker):
    async def fake_get_security_info(*args, **kwargs):
        class Security:
            symbol_name = "test"

        return Security()

    mocker.patch(
        "app.schedulers.ability.func.get_security_info",
        side_effect=fake_get_security_info,
    )
    stock_stats = await get_stock_stats(test_calculate_portfolio_ability)
    assert stock_stats[0]
