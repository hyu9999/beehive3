import pytest
from datetime import datetime

from app.crud.time_series_data import create_portfolio_assessment_time_series_data
from app.crud.user import get_user_by_username
from app.models.portfolio import Portfolio
from app.models.time_series_data import PortfolioAssessmentTimeSeriesDataInDB
from app.schema.user import User
from app.service.datetime import get_early_morning
from app.service.portfolio.portfolio_target import (
    PortfolioTargetTools,
    get_code_data,
    get_user_portfolio_targets,
)
from app.utils.datetime import date2datetime

pytestmark = pytest.mark.asyncio

CODE_RESULT_MAPPING = [
    ("10001", 41666.6667),
    ("10002", 1000000.0),
    ("10003", 0.0),
    ("10004", 1000000.0),
    ("10005", 1000000.0),
    ("10006", 0.0417),
    ("10007", 0.25),
    ("10008", 250000.0),
    ("10009", 0),
    ("100010", 0),
    ("100011", 0),
    ("100012", 0),
    ("100013", 0),
    ("100014", 0),
]


@pytest.mark.parametrize("code, result", CODE_RESULT_MAPPING)
async def test_get_code_data(
    code, result, fixture_db, portfolio_with_fund_time_series_data
):
    portfolio, fund_account, asset_time_series_data_list, days = portfolio_with_fund_time_series_data
    assessment_in_db = PortfolioAssessmentTimeSeriesDataInDB(
        portfolio=portfolio.id, tdate=date2datetime()
    )
    assessment = await create_portfolio_assessment_time_series_data(
        fixture_db, assessment_in_db
    )

    rv = await get_code_data(
        fixture_db,
        code,
        portfolio,
        assessment,
        fund_account,
        days[0],
        days[-1]
    )
    assert rv == result


async def test_get_config(fixture_db, logged_in_free_user):
    user = User(**logged_in_free_user["user"])
    rv = await PortfolioTargetTools.get_config(fixture_db, user)
    assert len(rv) == 2


async def test_get_row_data(fixture_db, portfolio_for_target_data: Portfolio):
    code_list = [item[0] for item in CODE_RESULT_MAPPING]
    rv = await PortfolioTargetTools.get_row_data(
        fixture_db, code_list, portfolio_for_target_data
    )
    assert len(rv) == len(code_list)


async def test_get_row_data_1(portfolio_with_fund_time_series_data, fixture_db):
    """验证在昨日没有生成指标数据的情况下函数是否运行正常."""
    portfolio, _, asset_time_series_data_list, _ = portfolio_with_fund_time_series_data
    tdate = get_early_morning()
    assessment_in_db = PortfolioAssessmentTimeSeriesDataInDB(portfolio=portfolio.id, tdate=tdate)
    await create_portfolio_assessment_time_series_data(fixture_db, assessment_in_db)
    assessment_in_db.tdate = datetime(2021, 5, 17)
    await create_portfolio_assessment_time_series_data(fixture_db, assessment_in_db)
    code_list = [item[0] for item in CODE_RESULT_MAPPING]
    rv = await PortfolioTargetTools.get_row_data(
        fixture_db, code_list, portfolio
    )
    assert len(rv) == len(code_list)


async def test_get_data(
    fixture_db, logged_in_free_user, portfolio_for_target_data: Portfolio
):
    user = User(**logged_in_free_user["user"])
    rv = await PortfolioTargetTools._get_data(
        fixture_db, portfolio_for_target_data, user
    )
    assert len(rv) == 2


async def test_get_data_list(
    fixture_db, logged_in_free_user, portfolio_for_target_data: Portfolio
):
    user = User(**logged_in_free_user["user"])
    rv = await PortfolioTargetTools.get_data_list(
        fixture_db, [portfolio_for_target_data], user
    )
    assert len(rv) == 1
    assert rv[0].portfolio.name == portfolio_for_target_data.name


async def test_get_user_target_data(fixture_db, portfolio_for_target_data: Portfolio):
    code_list = [item[0] for item in CODE_RESULT_MAPPING]
    rv = await PortfolioTargetTools.get_user_target_data(
        fixture_db, code_list, portfolio_for_target_data
    )
    assert len(rv.data_list) == len(code_list)


async def test_get_user_portfolio_targets(
    fixture_db, portfolio_for_target_data: Portfolio
):
    user = await get_user_by_username(fixture_db, portfolio_for_target_data.username)
    rv = await get_user_portfolio_targets(fixture_db, user)
    assert len(rv) == 1
    assert rv[0].user.username == user.username
    assert rv[0].data
