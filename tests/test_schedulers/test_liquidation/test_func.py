from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal

import pytest
from stralib import FastTdate

from app.core.errors import EntityDoesNotExist
from app.crud.fund_account import (
    create_fund_account_flow,
    create_fund_account_position,
    delete_fund_account_flow_many,
    get_fund_account_by_id,
    get_fund_account_flow_by_id,
    get_fund_account_flow_from_db,
    get_fund_account_position_by_id,
    get_fund_account_position_from_db,
    update_fund_account_by_id,
)
from app.crud.portfolio import delete_portfolio_many
from app.crud.time_series_data import create_position_time_series_data
from app.enums.fund_account import FlowTType
from app.models.base.time_series_data import Position
from app.models.fund_account import FundAccountFlowInDB, FundAccountPositionInDB
from app.models.rwmodel import PyDecimal
from app.models.time_series_data import PositionTimeSeriesDataInDB
from app.schedulers.liquidation.func import (
    liquidate_dividend_flow_task,
    liquidate_dividend_task,
    liquidate_dividend_tax_task,
    make_ts_position,
    reverse_flow,
    time_series_position2dividend,
    update_fund_account_by_flow,
    update_position_by_flow,
    update_time_series_position_data_by_flow,
)
from app.schema.fund_account import FundAccountInUpdate
from app.service.datetime import get_early_morning

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def auto_mocker(mocker):
    mocker.patch(
        "app.schedulers.liquidation.func.FastTdate.is_tdate", return_value=True
    )

    async def mock_check_status():
        return True

    async def mock_coro(*args, **kwargs):
        return 1

    mocker.patch(
        "app.schedulers.liquidation.func.CheckStatus.check_time_series_status",
        mock_check_status,
    )
    mocker.patch(
        "app.schedulers.liquidation.func.CheckStatus.check_liquidate_dividend_status",
        mock_check_status,
    )
    mocker.patch("app.schedulers.liquidation.func.liquidation_fund_asset", mock_coro)


def test_time_series_position2dividend():
    time_series_position = Position(
        symbol="600519", market="CNSESH", stkbal=1000, mktval="100000", buy_date=None
    )
    rv = time_series_position2dividend("-", time_series_position)
    assert rv.volume == time_series_position.stkbal


@pytest.mark.parametrize(
    "fundeffect, stkeffect",
    [
        (Decimal("100"), 100),
        (Decimal("-100"), -100),
        (Decimal("100"), -100),
        (Decimal("-100"), 100),
    ],
)
def test_reverse_flow(fund_account_flow_in_db, fundeffect, stkeffect):
    flow = deepcopy(fund_account_flow_in_db)
    flow.fundeffect = PyDecimal(fundeffect)
    flow.stkeffect = stkeffect
    rv = reverse_flow(flow)
    assert rv.fundeffect.to_decimal() == -fundeffect
    assert rv.stkeffect == -stkeffect


@pytest.mark.parametrize(
    "stkeffect",
    [
        1000,
        2000,
    ],
)
def test_make_ts_position(fund_account_flow_in_db, stkeffect):
    flow = deepcopy(fund_account_flow_in_db)
    flow.fundeffect = PyDecimal("0")
    flow.stkeffect = stkeffect
    rv = make_ts_position(flow)
    assert rv.stkbal == stkeffect


@pytest.mark.parametrize(
    "symbol, stkeffect, tdate, excepted_stkeffect",
    [
        ("600519", 1000, datetime(2021, 1, 1), 6000),
        ("600518", 1000, datetime(2021, 1, 1), 1000),
        ("600519", 1000, datetime(2021, 1, 2), 6000),
    ],
)
def test_update_time_series_position_data_by_flow(
    fund_account_flow_in_db,
    symbol,
    stkeffect,
    tdate,
    position_time_series_data,
    excepted_stkeffect,
):
    flow = deepcopy(fund_account_flow_in_db)
    flow.fundeffect = PyDecimal("0")
    flow.stkeffect = stkeffect
    flow.tdate = tdate
    flow.symbol = symbol
    ts_position = deepcopy(position_time_series_data)
    ts_position["tdate"] = datetime(2021, 1, 1)
    ts_position["position_list"] = [
        {
            "symbol": "600519",
            "market": "CNSESH",
            "stkbal": 5000,
            "mktval": "50000",
            "buy_date": datetime(2021, 1, 1),
        }
    ]
    ts_position = PositionTimeSeriesDataInDB(**ts_position)
    ts_position2 = deepcopy(ts_position)
    ts_position2.tdate = datetime(2021, 1, 3)
    ts_position_list = [ts_position, ts_position2]
    update_time_series_position_data_by_flow(ts_position_list, flow)
    for ts in ts_position_list:
        position = next(filter(lambda p: p.symbol == symbol, ts.position_list), None)
        if ts.tdate >= tdate:
            assert position.stkbal == excepted_stkeffect
        else:
            assert position.stkbal == 5000


@pytest.mark.parametrize(
    "symbol, record_dates, pay_dates, fundeffect_list, stkeffect_list",
    [
        (
            "600519",
            [datetime(2018, 6, 14), datetime(2019, 6, 27), datetime(2020, 6, 23)],
            [date(2018, 6, 15), date(2019, 6, 28), date(2020, 6, 24)],
            [Decimal("10999"), Decimal("14539"), Decimal("17025")],
            [0, 0, 0],
        ),
        (
            "002778",
            [datetime(2019, 6, 25), datetime(2020, 6, 16), datetime(2021, 6, 3)],
            [date(2019, 6, 26), date(2020, 6, 17), date(2021, 6, 4)],
            [Decimal("45"), Decimal("40"), Decimal("100")],
            [0, 0, 400],
        ),
    ],
)
async def test_liquidate_dividend_task(
    fixture_db,
    portfolio_with_fund_account,
    symbol,
    record_dates,
    pay_dates,
    fundeffect_list,
    stkeffect_list,
):
    portfolio, fund_account = portfolio_with_fund_account
    await delete_portfolio_many(fixture_db, {"_id": {"$ne": portfolio.id}})
    for record_date in record_dates:
        position = PositionTimeSeriesDataInDB(
            fund_id=str(fund_account.id),
            tdate=record_date,
            position_list=[
                {
                    "symbol": symbol,
                    "market": "CNSESH",
                    "stkbal": 1000,
                    "mktval": "100000",
                    "buy_date": record_dates[0],
                }
            ],
        )
        await create_position_time_series_data(fixture_db, position)
    fund_account_in_update = FundAccountInUpdate(**fund_account.dict())
    fund_account_in_update.ts_data_sync_date = datetime(2010, 1, 1)
    await update_fund_account_by_id(fixture_db, fund_account.id, fund_account_in_update)
    await liquidate_dividend_task()
    for index, pay_date in enumerate(pay_dates):
        flow = await get_fund_account_flow_from_db(
            fixture_db,
            fund_id=str(fund_account.id),
            ttype=[FlowTType.DIVIDEND],
            tdate=pay_date,
            symbol=symbol,
        )
        assert flow
        if len(flow) == 1:
            flow = flow[0]
            assert flow.fundeffect.to_decimal() == fundeffect_list[index]
            assert flow.stkeffect == stkeffect_list[index]
            assert flow.total_fee.to_decimal() == Decimal("0")
        else:
            assert len(flow) == 2
            assert (
                flow[0].fundeffect.to_decimal() + flow[1].fundeffect.to_decimal()
                == fundeffect_list[index]
            )
            assert flow[0].stkeffect + flow[1].stkeffect == stkeffect_list[index]
            assert flow[0].total_fee.to_decimal() + flow[
                1
            ].total_fee.to_decimal() == Decimal("0")


async def test_liquidate_dividend_task_with_ts_data_sync_date(
    portfolio_with_fund_account,
    fixture_db,
    fund_account_flow_in_db,
    fund_account_position_data,
):
    portfolio, fund_account = portfolio_with_fund_account
    await delete_portfolio_many(fixture_db, {"_id": {"$ne": portfolio.id}})
    record_dates = [datetime(2019, 6, 25), datetime(2020, 6, 16), datetime(2021, 6, 3)]
    for record_date in record_dates:
        position = PositionTimeSeriesDataInDB(
            fund_id=str(fund_account.id),
            tdate=record_date,
            position_list=[
                {
                    "symbol": "002778",
                    "market": "CNSESZ",
                    "stkbal": 1000,
                    "mktval": "100000",
                    "buy_date": record_dates[0],
                }
            ],
        )
        await create_position_time_series_data(fixture_db, position)
    fund_account_in_update = FundAccountInUpdate(**fund_account.dict())
    fund_account_in_update.ts_data_sync_date = datetime(2019, 6, 27)
    await update_fund_account_by_id(fixture_db, fund_account.id, fund_account_in_update)
    flow = deepcopy(fund_account_flow_in_db)
    flow.ttype = FlowTType.DIVIDEND
    flow.tdate = datetime(2020, 6, 17)
    flow.stkeffect = 100
    flow.fundeffect = PyDecimal("0")
    flow.fund_id = str(fund_account.id)
    flow.symbol = "002778"
    flow_in_db = await create_fund_account_flow(fixture_db, flow)
    position = FundAccountPositionInDB(**fund_account_position_data)
    position.symbol = "002778"
    position.fund_id = str(fund_account.id)
    position.volume = 1100
    await create_fund_account_position(fixture_db, position)

    await liquidate_dividend_task()

    # 验证多余的分红流水是否已删除
    with pytest.raises(EntityDoesNotExist):
        await get_fund_account_flow_by_id(fixture_db, flow_in_db.id)

    flow_list = await get_fund_account_flow_from_db(
        fixture_db,
        fund_id=str(fund_account.id),
        ttype=[FlowTType.DIVIDEND],
        tdate=datetime(2021, 6, 4),
    )
    for flow in flow_list:
        if flow.stkeffect:
            assert flow.stkeffect == 360
        else:
            assert flow.fundeffect.to_decimal() == Decimal("90")
    position_updated = await get_fund_account_position_from_db(
        fixture_db, fund_id=str(fund_account.id)
    )
    assert position_updated[0].volume == 1000


@pytest.mark.parametrize("fundeffect", (Decimal("0"), Decimal("100"), Decimal("150")))
async def test_update_fund_account_by_flow(
    fixture_db,
    portfolio_with_fund_account,
    fund_account_flow_in_db,
    fundeffect,
):
    _, fund_account = portfolio_with_fund_account
    await update_fund_account_by_flow(fixture_db, fund_account, fundeffect)
    updated_fund_account = await get_fund_account_by_id(fixture_db, fund_account.id)
    assert (
        updated_fund_account.cash.to_decimal() - fundeffect
        == fund_account.cash.to_decimal()
    )
    assert (
        updated_fund_account.assets.to_decimal() - fundeffect
        == fund_account.assets.to_decimal()
    )


@pytest.mark.parametrize(
    "fundeffect, stkeffect",
    (
        [Decimal("100"), 0],
        [Decimal("0"), 100],
        [Decimal("100"), 100],
    ),
)
async def test_update_position_by_flow(
    fixture_db, portfolio_with_position, fund_account_flow_in_db, fundeffect, stkeffect
):
    _, _, position_list = portfolio_with_position
    position = deepcopy(position_list[-1])
    position.cost = PyDecimal("500")
    flow = deepcopy(fund_account_flow_in_db)
    flow.ttype = FlowTType.DIVIDEND
    flow.fundeffect = PyDecimal(fundeffect)
    flow.stkeffect = stkeffect
    flow.tdate = datetime(2020, 6, 24)
    await update_position_by_flow(fixture_db, position, flow)
    updated_position = await get_fund_account_position_by_id(fixture_db, position.id)
    assert updated_position.volume - stkeffect == position_list[-1].volume
    assert (
        updated_position.available_volume - stkeffect
        == position_list[-1].available_volume
    )
    assert Decimal("500") - updated_position.cost.to_decimal() == Decimal("17.025")
    flow.stkeffect = -flow.stkeffect
    flow.fundeffect = PyDecimal(-flow.fundeffect.to_decimal())
    await update_position_by_flow(fixture_db, position, flow)
    updated_position_1 = await get_fund_account_position_by_id(fixture_db, position.id)
    assert updated_position_1.cost.to_decimal() == Decimal("500")


@pytest.mark.parametrize(
    "fundeffect, stkeffect",
    (
        [Decimal("100"), 0],
        [Decimal("0"), 100],
    ),
)
async def test_liquidate_dividend_flow_task(
    fixture_db,
    fund_account_flow_in_db,
    portfolio_with_fund_account,
    fundeffect,
    stkeffect,
    fund_account_position_data
):
    _, fund_account = portfolio_with_fund_account
    flow = deepcopy(fund_account_flow_in_db)
    flow.ttype = FlowTType.DIVIDEND
    flow.fundeffect = PyDecimal(fundeffect)
    flow.stkeffect = stkeffect
    flow.fund_id = str(fund_account.id)
    flow.tdate = get_early_morning().date()
    flow.symbol = "600519"
    flow.tdate = datetime(2020, 6, 24)
    fund_account_in_update = FundAccountInUpdate(**fund_account.dict())
    fund_account_in_update.ts_data_sync_date = FastTdate.last_tdate(flow.tdate)

    position = FundAccountPositionInDB(**fund_account_position_data)
    position.cost = PyDecimal("500")
    position.symbol = "600519"
    position.fund_id = str(fund_account.id)
    position.volume = 1000
    position = await create_fund_account_position(fixture_db, position)

    await update_fund_account_by_id(fixture_db, fund_account.id, fund_account_in_update)
    await delete_fund_account_flow_many(fixture_db, {})
    await create_fund_account_flow(fixture_db, flow)
    await liquidate_dividend_flow_task()
    updated_fund_account = await get_fund_account_by_id(fixture_db, fund_account.id)
    assert (
        updated_fund_account.cash.to_decimal() - fundeffect
        == fund_account.cash.to_decimal()
    )
    updated_position = await get_fund_account_position_by_id(fixture_db, position.id)
    assert updated_position.volume == position.volume + stkeffect


async def test_liquidate_dividend_tax_task(
    fixture_db, portfolio_with_fund_account, fund_account_position_data
):
    portfolio, fund_account = portfolio_with_fund_account
    await delete_portfolio_many(fixture_db, {"_id": {"$ne": portfolio.id}})
    flow_buy = FundAccountFlowInDB(
        fund_id=str(fund_account.id),
        symbol="600519",
        exchange="CNSESH",
        stkeffect=1000,
        cost="100",
        ttype=FlowTType.BUY,
        tdate=datetime(2020, 6, 23),
    )
    flow_sell = FundAccountFlowInDB(
        fund_id=str(fund_account.id),
        symbol="600519",
        exchange="CNSESH",
        stkeffect=-1000,
        cost="1000",
        ttype=FlowTType.SELL,
        tdate=datetime(2020, 6, 24),
    )
    await delete_fund_account_flow_many(fixture_db, {})
    await create_fund_account_flow(fixture_db, flow_buy)
    await create_fund_account_flow(fixture_db, flow_sell)
    fund_account_in_update = FundAccountInUpdate(**fund_account.dict())
    fund_account_in_update.ts_data_sync_date = FastTdate.last_tdate(
        datetime(2020, 6, 23)
    )
    await update_fund_account_by_id(fixture_db, fund_account.id, fund_account_in_update)

    position = FundAccountPositionInDB(**fund_account_position_data)
    position.cost = PyDecimal("500")
    position.symbol = "600519"
    position.fund_id = str(fund_account.id)
    position.volume = 1000
    position = await create_fund_account_position(fixture_db, position)

    await liquidate_dividend_tax_task()
    tax_flow = await get_fund_account_flow_from_db(
        fixture_db, fund_id=str(fund_account.id), ttype=[FlowTType.TAX]
    )
    assert tax_flow
    tax_flow = tax_flow[0]
    assert tax_flow.stkeffect == 0
    assert tax_flow.fundeffect.to_decimal() == Decimal("-3405")
    assert tax_flow.tdate == flow_sell.tdate

    updated_fund_account = await get_fund_account_by_id(fixture_db, fund_account.id)
    assert (
        fund_account.cash.to_decimal() - updated_fund_account.cash.to_decimal()
        == Decimal("3405")
    )
    assert (
        fund_account.assets.to_decimal() - updated_fund_account.assets.to_decimal()
        == Decimal("3405")
    )

    updated_position = await get_fund_account_position_by_id(fixture_db, position.id)
    assert updated_position.cost.to_decimal() == Decimal("503.405")
