from copy import deepcopy
from datetime import timedelta

import pytest
from stralib import FastTdate

from app.crud.fund_account import create_fund_account_flow, create_fund_account_position
from app.models.fund_account import FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.schema.user import User
from app.service.datetime import get_early_morning
from app.service.portfolio.stock_statistics import StockStatisticsTools, get_trade_num

pytestmark = pytest.mark.asyncio


async def test_get_config(fixture_db, logged_in_free_user):
    user = User(**logged_in_free_user["user"])
    rv = await StockStatisticsTools.get_config(fixture_db, user)
    assert len(rv) == 2


async def test_get_data(
    fixture_db,
    portfolio_in_db: Portfolio,
    fund_account_position_data,
    fund_account_flow_list,
):
    fund_id = portfolio_in_db.fund_account[0].fundid
    position_data = deepcopy(fund_account_position_data)
    position_data["fund_id"] = fund_id
    position_data["symbol"] = "601816"
    await create_fund_account_position(
        fixture_db, FundAccountPositionInDB(**position_data)
    )
    flow_data = deepcopy(fund_account_flow_list)
    for flow in flow_data:
        flow.fund_id = fund_id
        await create_fund_account_flow(fixture_db, flow)
    tdate = get_early_morning()
    *_, day1, _, _, day4 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )
    rv = await StockStatisticsTools.get_data(fixture_db, portfolio_in_db, day1, day4)
    assert len(rv) == 1
    assert rv[0]["symbol"] == position_data["symbol"]
    assert rv[0]["data"]


async def test_get_trade_num(
    fixture_db, portfolio_with_flow: Portfolio, fund_account_flow_data
):
    tdate = get_early_morning()
    rv = await get_trade_num(
        fixture_db,
        portfolio_with_flow.fund_account[0],
        tdate,
        tdate,
        fund_account_flow_data["symbol"],
        portfolio_with_flow,
    )
    assert rv == 1
