from decimal import Decimal

import pandas as pd
import pytest
from stralib import FastTdate

from app.enums.fund_account import CurrencyType, FlowTType
from app.enums.portfolio import PortfolioCategory
from app.models.fund_account import (
    FundAccountFlowInDB,
    FundAccountInDB,
    FundAccountPositionInDB,
)
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyDecimal, PyObjectId
from app.schema.fund_account import FundAccountFlowInCreate
from app.schema.portfolio import PortfolioInResponse
from app.service.datetime import get_early_morning
from app.service.fund_account.fund_account import (
    calculate_flow_fee,
    calculate_fund_asset,
    calculation_simple,
    calculation_simple_ability,
    generate_simulation_account,
    get_fund_account_flow,
    get_fund_account_position,
    get_fund_asset,
    get_net_deposit_flow,
    get_portfolio_fund_list,
    get_portfolio_position,
    set_portfolio_import_date,
    update_fund_account_by_flow,
    update_position_by_flow,
)

pytestmark = pytest.mark.asyncio


async def test_generate_simulation_account(fixture_db):
    portfolio_id = "test_portfolio_id"
    fund_account = await generate_simulation_account(
        portfolio_id=portfolio_id, total_input=100000
    )
    assert fund_account.userid == portfolio_id


@pytest.mark.parametrize("ttype,", [FlowTType.BUY, FlowTType.SELL])
def test_calculate_flow_fee(
    ttype, fund_account_flow_data, fixture_db, fund_account_data
):
    fund_account = FundAccountInDB(**fund_account_data)

    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype=ttype)
    flow_in_db = calculate_flow_fee(fund_account, flow)
    if ttype == FlowTType.BUY:
        assert flow_in_db.fundeffect.to_decimal() < 0
        assert flow_in_db.stkeffect > 0
        assert flow_in_db.tax.to_decimal() == Decimal("0")
        assert flow_in_db.total_fee == flow_in_db.commission
    else:
        assert flow_in_db.fundeffect.to_decimal() > 0
        assert flow_in_db.stkeffect < 0
        assert (
            flow_in_db.total_fee.to_decimal()
            == flow_in_db.tax.to_decimal() + flow_in_db.commission.to_decimal()
        )
    # 交易费用 = 额外平摊成本 * 成交数量
    # 因为计算出的成交价格有一定误差，所以用减的方式来判断是否大约相等
    assert flow_in_db.total_fee.to_decimal() - (
        (flow.cost.to_decimal() - flow_in_db.tprice.to_decimal())
        * abs(flow_in_db.stkeffect)
    ) < (abs(flow.stkeffect) * flow.cost.to_decimal()) / Decimal("0.001")


async def test_update_fund_account_by_flow(
    mocker,
    fund_account_flow_data,
    fixture_db,
    fund_account_position_data,
    fund_account_data,
):
    fund_account = FundAccountInDB(**fund_account_data)

    async def fake_position(*args, **kwargs):
        return [FundAccountPositionInDB(**fund_account_position_data)]

    async def fake_price(*args, **kwargs):
        class FakeSecurity:
            current = Decimal("10")

        return FakeSecurity()

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_position_from_db",
        side_effect=fake_position,
    )
    mocker.patch(
        "app.service.fund_account.fund_account.get_security_price",
        side_effect=fake_price,
    )

    async def coro(*args, **kwargs):
        return None

    update = mocker.patch(
        "app.service.fund_account.fund_account.update_fund_account_by_id",
        side_effect=coro,
    )
    flow = FundAccountFlowInDB(**fund_account_flow_data, ttype=FlowTType.BUY)
    await update_fund_account_by_flow(fixture_db, fund_account, flow)
    assert update.called


@pytest.mark.parametrize("has_position,", [True, False])
async def test_update_position_by_flow(
    has_position, mocker, fixture_db, fund_account_flow_data
):
    async def fake_get_fund_account_position(*args, **kwargs):
        class FakePosition:
            volume = 10000
            cost = PyDecimal("10")
            id = PyObjectId("60122d282c27e2a494940a36")

        return [FakePosition()] if has_position else None

    async def coro(*args, **kwargs):
        return None

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_position_from_db",
        side_effect=fake_get_fund_account_position,
    )
    delete = mocker.patch(
        "app.service.fund_account.fund_account.delete_fund_account_position_by_id",
        side_effect=coro,
    )
    update = mocker.patch(
        "app.service.fund_account.fund_account.update_fund_account_position_by_id",
        side_effect=coro,
    )
    create = mocker.patch(
        "app.service.fund_account.fund_account.create_fund_account_position",
        side_effect=coro,
    )

    # 买单
    # 验证一切正常时是否会创建或更新持仓
    flow = FundAccountFlowInDB(**fund_account_flow_data, ttype=FlowTType.BUY)
    await update_position_by_flow(fixture_db, flow)
    if not has_position:
        assert create.called
    else:
        assert update.called

    # 卖单
    fund_account_flow_data["stkeffect"] = -10001
    # 验证当出售数量大于持仓数量时是否会触发异常
    if has_position:
        # 验证当出售数量等于持仓数量时是否会删除持仓
        fund_account_flow_data["stkeffect"] = -10000
        flow = FundAccountFlowInDB(**fund_account_flow_data, ttype=FlowTType.SELL)
        await update_position_by_flow(fixture_db, flow)
        assert delete.called


@pytest.mark.parametrize(
    "category,", [PortfolioCategory.ManualImport, PortfolioCategory.SimulatedTrading]
)
async def test_get_fund_account_position(
    mocker, fund_account_position_data, fixture_db, fund_account_data, category
):
    async def fake_get_fund_account_position_from_db(*args, **kwargs):
        return [FundAccountPositionInDB(**fund_account_position_data)]

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_position_from_db",
        side_effect=fake_get_fund_account_position_from_db,
    )
    portfolio_position = await get_fund_account_position(
        fixture_db, fund_account_data["_id"], category
    )
    assert portfolio_position[0].exchange


@pytest.mark.parametrize(
    "category,", [PortfolioCategory.ManualImport, PortfolioCategory.SimulatedTrading]
)
async def test_get_portfolio_fund_list(
    mocker, portfolio_data_in_db, fund_account_data, fixture_db, category
):
    portfolio_data_in_db["category"] = category
    portfolio_data_in_db["fund_account"][0]["fundid"] = str(PyObjectId())
    portfolio_in_response = PortfolioInResponse(**portfolio_data_in_db)

    async def coro(*args, **kwargs):
        return portfolio_in_response

    mocker.patch(
        "app.service.fund_account.fund_account.get_portfolio_by_id", side_effect=coro
    )

    async def fake_get_fund_account_by_id(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_by_id",
        side_effect=fake_get_fund_account_by_id,
    )
    portfolio_fund = await get_portfolio_fund_list(fixture_db, PyObjectId())
    assert portfolio_fund[0].currency


@pytest.mark.parametrize(
    "category,", [PortfolioCategory.ManualImport, PortfolioCategory.SimulatedTrading]
)
async def test_get_fund_account_flow(
    mocker, category, fixture_db, fund_account_flow_data
):
    async def fake_get_fund_account_flow_from_db(*args, **kwargs):
        return [FundAccountFlowInDB(**fund_account_flow_data, ttype=FlowTType.BUY)]

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_flow_from_db",
        side_effect=fake_get_fund_account_flow_from_db,
    )
    flow = await get_fund_account_flow(
        fixture_db, "5face26c57fbb548227231d5", category, currency=CurrencyType.CNY
    )
    assert flow[0].currency


async def test_get_portfolio_position(
    mocker,
    fixture_db,
    portfolio_data_in_db,
    fund_account_position_data,
):
    portfolio_in_response = PortfolioInResponse(**portfolio_data_in_db)

    async def coro(*args, **kwargs):
        return portfolio_in_response

    mocker.patch(
        "app.service.fund_account.fund_account.get_portfolio_by_id", side_effect=coro
    )

    async def fake_get_fund_account_position(*args, **kwargs):
        return [FundAccountPositionInDB(**fund_account_position_data)]

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_position",
        side_effect=fake_get_fund_account_position,
    )
    await get_portfolio_position(fixture_db, PyObjectId())


@pytest.mark.parametrize(
    "category,", [PortfolioCategory.ManualImport, PortfolioCategory.SimulatedTrading]
)
async def test_get_fund_asset(
    mocker,
    category,
    fund_account_data,
    fixture_db,
):
    async def fake_get_fund_account_by_id(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_by_id",
        side_effect=fake_get_fund_account_by_id,
    )
    asset = await get_fund_asset(
        fixture_db, "607799f381a6ac32588fbe08", category, CurrencyType.CNY
    )
    assert asset.cash


async def test_calculate_fund_asset(
    mocker, fixture_db, fund_account_position_data, fund_account_data
):
    fund_account_in_db = FundAccountInDB(**fund_account_data)

    async def fake_get_fund_account_position_from_db(*args, **kwargs):
        return [FundAccountPositionInDB(**fund_account_position_data)]

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_position_from_db",
        side_effect=fake_get_fund_account_position_from_db,
    )

    async def fake_get_security_price(*args, **kwargs):
        class FakeSecurityPrice:
            current = Decimal(10)

        return FakeSecurityPrice()

    mocker.patch(
        "app.service.fund_account.fund_account.get_security_price",
        side_effect=fake_get_security_price,
    )
    fund_account = await calculate_fund_asset(fixture_db, fund_account_in_db)
    assert (
        fund_account.securities.to_decimal()
        == Decimal(10) * fund_account_position_data["volume"]
    )


async def test_set_portfolio_import_date(
    mocker, fixture_db, fund_account_data, fund_account_flow_data, portfolio_data_in_db
):
    fund_account_in_db = FundAccountInDB(**fund_account_data)

    async def fake_get_fund_account_flow_from_db(*args, **kwargs):
        return [FundAccountFlowInDB(**fund_account_flow_data, ttype=FlowTType.BUY)]

    mocker.patch(
        "app.service.fund_account.fund_account.get_fund_account_flow_from_db",
        side_effect=fake_get_fund_account_flow_from_db,
    )

    async def fake_get_portfolio_by_fund_id(*args, **kwargs):
        return Portfolio(**portfolio_data_in_db)

    mocker.patch(
        "app.service.fund_account.fund_account.get_portfolio_by_fund_id",
        side_effect=fake_get_portfolio_by_fund_id,
    )

    async def coro(*args, **kwargs):
        ...

    mocker.patch(
        "app.service.fund_account.fund_account.update_portfolio_import_date_by_id",
        side_effect=coro,
    )
    await set_portfolio_import_date(fixture_db, fund_account_in_db)


async def test_get_net_deposit_flow(fixture_db, portfolio_with_flow: Portfolio):
    tdate = get_early_morning()
    start_date = FastTdate.last_tdate(tdate)
    rv = await get_net_deposit_flow(fixture_db, portfolio_with_flow, start_date, tdate)
    assert rv.size == 1


def test_calculation_simple():
    assets_list = pd.Series({"2021-01-01": 100000, "2021-01-02": 0, "2021-01-03": 0})
    net_deposit_list = pd.Series({"2021-01-02": -100000})
    rv = calculation_simple(net_deposit_list, assets_list)
    assert rv == 0


def test_calculation_simple2():
    dt = {
        "2021-02-26": 100000.0,
        "2021-03-01": 100000.0,
        "2021-03-02": 106797.6,
        "2021-03-03": 106598.6,
        "2021-03-04": 105608.6,
        "2021-03-05": 105742.6,
        "2021-03-08": 104748.6,
        "2021-03-09": 104198.6,
        "2021-03-10": 104145.2,
        "2021-03-11": 105842.2,
        "2021-03-12": 109650.2,
        "2021-03-15": 109624.2,
        "2021-03-16": 110649.2,
        "2021-03-17": 109988.2,
        "2021-03-18": 111836.2,
        "2021-03-19": 112509.2,
        "2021-03-22": 109904.2,
        "2021-03-23": 110995.2,
        "2021-03-24": 107572.2,
        "2021-03-25": 108301.2,
        "2021-03-26": 109469.2,
        "2021-03-29": 113282.2,
        "2021-03-30": 115086.2,
        "2021-03-31": 116304.2,
        "2021-04-01": 116289.2,
        "2021-04-02": 117042.2,
        "2021-04-06": 117826.2,
        "2021-04-07": 118186.2,
        "2021-04-08": 115567.2,
        "2021-04-09": 117651.2,
        "2021-04-12": 117187.2,
        "2021-04-13": 115133.2,
        "2021-04-14": 118313.2,
        "2021-04-15": 116418.2,
        "2021-04-16": 115921.2,
        "2021-04-19": 113456.2,
        "2021-04-20": 113617.2,
        "2021-04-21": 113680.2,
        "2021-04-22": 112553.2,
        "2021-04-23": 111806.2,
        "2021-04-26": 112522.2,
        "2021-04-27": 112798.2,
        "2021-04-28": 112827.2,
        "2021-04-29": 112607.2,
        "2021-04-30": 112252.2,
        "2021-05-06": 111545.2,
        "2021-05-07": 110451.2,
        "2021-05-10": 1109181.2,
        "2021-05-11": 1108982.2,
        "2021-05-12": 1108982.2,
    }

    assets_list = [
        107927.2,
        1108923.2,
        1109181.2,
        110451.2,
        111545.2,
        112252.2,
        112607.2,
        112827.2,
        112798.2,
        112522.2,
        111806.2,
        112553.2,
        113680.2,
        113617.2,
        113456.2,
        115921.2,
        116418.2,
        118313.2,
        115133.2,
        117187.2,
        117651.2,
        115567.2,
        118186.2,
        117826.2,
        112354.2,
        111528.2,
        111705.2,
        110525.2,
        109463.2,
        105628.2,
        104802.2,
        104094.2,
        107339.2,
        106100.2,
        108814.2,
        107752.2,
        105923.2,
        106690.2,
        105628.2,
        104743.2,
        101144.2,
        99846.2,
        99999.6,
        99999.6,
        99999.6,
        99999.6,
        99999.6,
        99999.6,
        99999.6,
        99999.6,
    ]
    index = 0
    assets_list.reverse()
    for k, v in dt.items():
        dt[k] = assets_list[index]
        index += 1
    assets_list_1 = pd.Series(
        dt,
        name="股票资产",
    )
    net_deposit_list = pd.Series(
        {
            "2021-05-10": 1000000,
            "2021-05-12": -1000000,
        },
        name="当日净入金_中间值",
    )
    rv = calculation_simple_ability(net_deposit_list, assets_list_1)
    assert round(rv, 4) == 0.102
