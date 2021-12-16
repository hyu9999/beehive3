from datetime import datetime

import pytest
from stralib import FastTdate

from app.crud.time_series_data import (
    get_fund_time_series_data,
    get_portfolio_assessment_time_series_data,
    get_position_time_series_data,
)
from app.service.time_series_data.time_series_data import (
    create_init_time_series_data,
    get_assets_time_series_data,
)

pytestmark = pytest.mark.asyncio


async def test_get_assets_time_series_data(
    fixture_db,
    portfolio_with_fund_time_series_data,
):
    (
        portfolio,
        _,
        fund_time_series_data_list,
        tdate_list,
    ) = portfolio_with_fund_time_series_data
    day1, _, _, day4 = tdate_list
    rv = await get_assets_time_series_data(fixture_db, portfolio, day1, day4)
    assert rv.size == len(fund_time_series_data_list)
    assert (
        list(rv.keys()).sort()
        == [item.tdate for item in fund_time_series_data_list].sort()
    )


async def test_get_assets_time_series_data_today(
    fixture_db,
    portfolio_with_fund_time_series_data,
):
    (
        portfolio,
        _,
        fund_time_series_data_list,
        tdate_list,
    ) = portfolio_with_fund_time_series_data
    day1, _, _, day4 = tdate_list
    rv = await get_assets_time_series_data(
        fixture_db, portfolio, day1, datetime.today().date()
    )
    assert rv.size == len(fund_time_series_data_list) + 1
    assert (
        list(rv.keys()).sort()
        == (
            [item.tdate for item in fund_time_series_data_list] + [datetime.today()]
        ).sort()
    )


async def test_create_init_time_series_data(
    fixture_db,
    portfolio_with_fund_account,
):
    portfolio, fund_account = portfolio_with_fund_account
    await create_init_time_series_data(fixture_db, portfolio)
    tdate = FastTdate.last_tdate(datetime.today())
    fund_id = str(fund_account.id)
    fund_time_series_data = await get_fund_time_series_data(
        fixture_db, fund_id=fund_id, tdate=tdate.date()
    )
    assert fund_time_series_data
    position_time_series_data = await get_position_time_series_data(
        fixture_db, fund_id=fund_id, tdate=tdate.date()
    )
    assert position_time_series_data

    portfolio_assessment_time_series_data = (
        await get_portfolio_assessment_time_series_data(
            fixture_db, portfolio=portfolio.id, tdate=tdate.date()
        )
    )
    assert portfolio_assessment_time_series_data
