from copy import deepcopy

import pytest

from app.crud.fund_account import create_fund_account_flow
from app.crud.time_series_data import create_portfolio_assessment_time_series_data
from app.enums.fund_account import FlowTType
from app.models.portfolio import Portfolio
from app.models.time_series_data import PortfolioAssessmentTimeSeriesDataInDB
from app.schema.user import User
from app.service.portfolio.trade_statistics import TradeStatisticsTools

pytestmark = pytest.mark.asyncio


async def test_get_config(fixture_db, logged_in_free_user):
    user = User(**logged_in_free_user["user"])
    rv = await TradeStatisticsTools.get_config(fixture_db, user.username)
    assert len(rv) == 2


@pytest.fixture
async def portfolio_with_assessment(
    fixture_db,
    portfolio_in_db: Portfolio,
    fund_account_flow_list,
):
    fund_id = portfolio_in_db.fund_account[0].fundid
    flow_data = deepcopy(fund_account_flow_list)
    for flow in flow_data:
        flow.fund_id = fund_id
        await create_fund_account_flow(fixture_db, flow)
    flow = flow_data[-1]
    flow.ttype = FlowTType.SELL
    await create_fund_account_flow(fixture_db, flow)
    tdate_list = [flow.tdate for flow in flow_data]
    assessment_in_db = PortfolioAssessmentTimeSeriesDataInDB(
        portfolio=portfolio_in_db.id, tdate=tdate_list[-1]
    )
    assessment_in_db.winning_rate = 10
    assessment_in_db.trade_cost = 5
    assessment_in_db.profit_loss_ratio = 3
    assessment = await create_portfolio_assessment_time_series_data(
        fixture_db, assessment_in_db
    )
    return portfolio_in_db, tdate_list, assessment


async def test_get_data(fixture_db, portfolio_with_assessment):
    portfolio, tdate_list, assessment = portfolio_with_assessment
    rv = await TradeStatisticsTools.get_data(
        fixture_db, portfolio, tdate_list[0], tdate_list[-1]
    )
    assert rv["portfolio_data"][0]["value"] == assessment.trade_cost
    assert rv["portfolio_data"][1]["value"] == assessment.winning_rate


async def test_get_data_1(fixture_db, portfolio_with_assessment):
    portfolio, tdate_list, assessment = portfolio_with_assessment
    rv = await TradeStatisticsTools._get_data(
        fixture_db, portfolio, tdate_list[0], tdate_list[-1]
    )
    assert rv[0]["value"] == assessment.trade_cost
    assert rv[1]["value"] == assessment.winning_rate


@pytest.mark.parametrize(
    "row_name, result",
    [
        ("winning_rate", 10),
        ("profit_loss_ratio", 3),
        ("trade_cost", 5),
        ("trade_frequency", 2),
    ],
)
async def test_get_row_data(fixture_db, row_name, portfolio_with_assessment, result):
    portfolio, tdate_list, assessment = portfolio_with_assessment
    rv = await TradeStatisticsTools.get_row_data(
        fixture_db, row_name, [portfolio.id], tdate_list[0], tdate_list[-1]
    )
    assert rv == result
