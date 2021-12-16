from copy import deepcopy
from datetime import timedelta
from decimal import Decimal

import pandas as pd
import pytest
from pytest import mark
from stralib import FastTdate

from app.core.errors import PortfolioTooMany
from app.enums.common import DateType
from app.enums.portfolio import PortfolioCategory, ReturnYieldCalculationMethod
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.models.time_series_data import PortfolioAssessmentTimeSeriesDataInDB
from app.schema.equipment import 装备InResponse
from app.schema.portfolio import PortfolioInResponse
from app.schema.user import User
from app.service.portfolio.portfolio import (
    PortfolioTools,
    get_account_asset,
    get_account_position,
    get_account_stock_position,
    get_date_by_type,
    get_portfolio_profit_rate,
    get_portfolio_yield_trend,
    get_yield_trend,
    inspect_portfolio_number_limit,
)
from app.utils.datetime import date2datetime

pytestmark = pytest.mark.asyncio


async def test_inspect_portfolio_number_limit(
    mocker,
    fixture_db,
    fixture_settings,
    logined_vip_user,
):
    num_limit = fixture_settings.num_limit["VIP用户"]["portfolio"]

    def fake_get_portfolio_collection(*args, **kwargs):
        class FakeDoc:
            @staticmethod
            async def count_documents(*args, **kwargs):
                return num_limit - 1

        return FakeDoc()

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_collection",
        side_effect=fake_get_portfolio_collection,
    )
    user = User(
        **logined_vip_user,
        username="test",
        status="normal",
        id=PyObjectId(),
        roles=["VIP用户"],
    )
    await inspect_portfolio_number_limit(fixture_db, user)
    with pytest.raises(PortfolioTooMany):
        num_limit = 11
        await inspect_portfolio_number_limit(fixture_db, user)


def test_get_date_by_type():
    assert get_date_by_type(DateType.DAY)


async def test_get_portfolio_yield_trend(
    mocker,
    fixture_db,
    portfolio_data_in_db,
):
    portfolio = Portfolio(**portfolio_data_in_db)
    tdate = date2datetime()
    *_, start_date, day1, day2, end_date = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )

    async def fake_get_portfolio_assessment_time_series_data(conn, portfolio, tdate):

        tdate_yield_mapping = {
            start_date.date(): 0,
            day1.date(): 1,
            day2.date(): 2,
            end_date.date(): 3,
        }

        class Assessment:
            account_yield = tdate_yield_mapping[tdate]

        return [Assessment()]

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_assessment_time_series_data",
        side_effect=fake_get_portfolio_assessment_time_series_data,
    )
    data_list = await get_portfolio_yield_trend(
        fixture_db, portfolio, start_date=start_date, end_date=end_date
    )
    assert [data["profit_rate"] for data in data_list] == [0, 1, 2, 3]


async def test_get_yield_trend(
    mocker,
    fixture_db,
    portfolio_data_in_db,
):
    async def fake_get_portfolio_by_id(*args, **kwargs):
        return Portfolio(**portfolio_data_in_db)

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_by_id",
        side_effect=fake_get_portfolio_by_id,
    )

    async def coro(*args, **kwargs):
        return 1

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_yield_trend", side_effect=coro
    )
    data = await get_yield_trend(
        fixture_db,
        portfolio_data_in_db["_id"],
        start_date=date2datetime(),
        end_date=date2datetime(),
    )
    assert data["data_list"] == 1


async def test_get_account_asset(
    mocker, fixture_db, portfolio_data_in_db, fund_account_data
):
    async def fake_get_portfolio_by_id(*args, **kwargs):
        return Portfolio(**portfolio_data_in_db)

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_by_id",
        side_effect=fake_get_portfolio_by_id,
    )

    async def fake_liquidation_fund_asset(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.service.portfolio.portfolio.liquidation_fund_asset",
        side_effect=fake_liquidation_fund_asset,
    )

    async def fake_get_fund_asset(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.service.portfolio.portfolio.get_fund_asset",
        side_effect=fake_get_fund_asset,
    )

    async def fake_db_asset2frontend(_, fund_asset: FundAccountInDB, *args):
        asset_dict = fund_asset.dict()
        asset_dict["total_profit_rate"] = 0
        return asset_dict

    mocker.patch(
        "app.service.portfolio.portfolio.db_asset2frontend",
        side_effect=fake_db_asset2frontend,
    )
    asset = await get_account_asset(fixture_db, PyObjectId())
    assert isinstance(asset, dict)
    assert asset["total_profit_rate"] == 0
    calculate = mocker.patch(
        "app.service.portfolio.portfolio.calculate_fund_asset",
        side_effect=fake_get_fund_asset,
    )

    async def coro(*args, **kwargs):
        ...

    update = mocker.patch(
        "app.service.portfolio.portfolio.update_fund_account_by_id", side_effect=coro
    )
    portfolio_data_in_db["category"] = PortfolioCategory.ManualImport
    await get_account_asset(fixture_db, PyObjectId(), refresh=True)
    assert calculate.called
    assert update.called


@pytest.mark.skip()
async def test_get_account_stock_position(
    mocker,
    fixture_db,
    portfolio_data_in_db,
    fund_account_position_data,
):
    async def fake_get_portfolio_by_id(*args, **kwargs):
        return Portfolio(**portfolio_data_in_db)

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_by_id",
        side_effect=fake_get_portfolio_by_id,
    )

    async def fake_get_fund_account_position(*args, **kwargs):
        return [FundAccountPositionInDB(**fund_account_position_data)]

    mocker.patch(
        "app.service.portfolio.portfolio.get_fund_account_position",
        side_effect=fake_get_fund_account_position,
    )
    position = await get_account_stock_position(
        fixture_db, PyObjectId(), symbol=fund_account_position_data["symbol"]
    )
    assert isinstance(position, dict)
    assert position["symbol"] == fund_account_position_data["symbol"]
    position = await get_account_stock_position(
        fixture_db, PyObjectId(), symbol=fund_account_position_data["symbol"] + "x"
    )
    assert not position


@mark.skip
async def test_get_account_position(
    mocker, fixture_db, portfolio_data_in_db, fund_account_position_data
):
    portfolio = PortfolioInResponse(**portfolio_data_in_db)

    async def fake_get_fund_account_position(*args, **kwargs):
        return [FundAccountPositionInDB(**fund_account_position_data)]

    mocker.patch(
        "app.service.portfolio.portfolio.get_fund_account_position",
        side_effect=fake_get_fund_account_position,
    )
    position_list = await get_account_position(fixture_db, portfolio)
    assert len(position_list) == 1
    assert position_list[0]["symbol"] == fund_account_position_data["symbol"]


@pytest.mark.parametrize(
    "calculation_method",
    [ReturnYieldCalculationMethod.TWR, ReturnYieldCalculationMethod.MWR],
)
async def test_basic_run_data(
    mocker, fixture_db, portfolio_data_in_db, fund_account_data, calculation_method
):
    async def fake_get_portfolio_by_id(*args, **kwargs):
        return Portfolio(**portfolio_data_in_db)

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_by_id",
        side_effect=fake_get_portfolio_by_id,
    )

    async def fake_get_fund_asset(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.service.portfolio.portfolio.get_fund_asset",
        side_effect=fake_get_fund_asset,
    )

    async def fake_get_portfolio_profit_rate(*args, **kwargs):
        return 0

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_profit_rate",
        side_effect=fake_get_portfolio_profit_rate,
    )

    async def fake_get_portfolio_assessment_time_series_data(*args, **kwargs):
        return [
            PortfolioAssessmentTimeSeriesDataInDB(
                portfolio=PyObjectId(), tdate=date2datetime(), annual_rate=1
            )
        ]

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_assessment_time_series_data",
        side_effect=fake_get_portfolio_assessment_time_series_data,
    )
    data = await PortfolioTools.basic_run_data(
        fixture_db, PyObjectId(), calculation_method
    )
    assert data
    assert data.profit_rate == 0
    assert data.expected_reach_date


async def test_get_position(
    mocker,
    fixture_db,
    portfolio_data_in_db,
    fund_account_position_data,
    fund_account_data,
):
    async def fake_get_portfolio_by_id(*args, **kwargs):
        return PortfolioInResponse(**portfolio_data_in_db)

    mocker.patch(
        "app.service.portfolio.portfolio.get_portfolio_by_id",
        side_effect=fake_get_portfolio_by_id,
    )

    async def fake_get_fund_account_position(*args, **kwargs):
        p1 = FundAccountPositionInDB(**fund_account_position_data)
        p2 = deepcopy(p1)
        p2.symbol = "000001"
        p2.exchange = "CNSESZ"
        return [p1, p2]

    mocker.patch(
        "app.service.portfolio.portfolio.get_fund_account_position",
        side_effect=fake_get_fund_account_position,
    )

    async def fake_hq(*args, **kwargs):
        class Security:
            symbol_name = ""
            industry = "industry_1"
            current = Decimal("100")

        return Security()

    mocker.patch(
        "app.service.fund_account.converter.get_security_hq", side_effect=fake_hq
    )

    async def fake_get_fund_asset(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.service.portfolio.portfolio.get_fund_asset",
        side_effect=fake_get_fund_asset,
    )
    data = await PortfolioTools.get_position(fixture_db, PyObjectId())
    assert len(data["industry_info"]) == 1
    assert data["industry_info"][0]["name"] == "industry_1"
    assert len(data["industry_info"][0]["stocks"]) == 2


@mark.skip
async def test_get_stock_risk_level(mocker, fixture_db, risk_equipments_data):
    async def fake_get_equipment_detail(*args, **kwargs):
        risk_equipments_data[0]["作者"] = {"id": PyObjectId(), "username": ""}
        return 装备InResponse(**risk_equipments_data[0])

    mocker.patch(
        "app.service.portfolio.portfolio.查询某个装备的详情",
        side_effect=fake_get_equipment_detail,
    )

    def mock_get_strategy_signal(*args):
        return pd.DataFrame(
            {"grade": 1, "symbol": "600519"},
            pd.Index(["grade", "symbol"]),
        )

    mocker.patch(
        "app.service.portfolio.portfolio.get_strategy_signal",
        side_effect=mock_get_strategy_signal,
    )
    data = await PortfolioTools.get_stock_risk_level(
        fixture_db, robot={"风控装备列表": ["03"]}, stock={"symbol": "600519"}
    )
    assert data[0]["grade"] == 1


@pytest.mark.skip
@pytest.mark.parametrize(
    "method, result",
    [
        (ReturnYieldCalculationMethod.SWR, 0.25),
        (ReturnYieldCalculationMethod.TWR, 0.25),
        (ReturnYieldCalculationMethod.MWR, -0.167),
    ],
)
async def test_get_portfolio_profit_rate(
    fixture_db, portfolio_with_fund_time_series_data, method, result
):
    (
        portfolio,
        _,
        fund_time_series_data_list,
        tdate_list,
    ) = portfolio_with_fund_time_series_data
    day1, _, _, day4 = tdate_list
    portfolio.import_date = date2datetime(day1)
    rv = await get_portfolio_profit_rate(fixture_db, portfolio, day1, day4, method)
    assert round(rv, 3) == result
