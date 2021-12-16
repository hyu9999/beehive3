from datetime import datetime

from pytest import mark

from app.crud.portfolio import get_portfolio_by_id
from app.enums.fund_account import Exchange
from app.enums.portfolio import 风险点状态
from app.enums.solution import SolutionStepEnum
from app.models.fund_account import FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.schema.signal import TimingStrategySignalInResponse
from app.service.risks.risk import (
    finish_portfolio_risks,
    get_all_risks,
    get_position_risks_step,
    ignore_abnormal_risks,
)
from tests.mocks.robot import mock_robot

pytestmark = mark.asyncio


async def test_get_position_risks_step(
    fixture_client,
    fixture_portfolio_underweight_risk,
    fixture_portfolio_overweight_risk,
):
    #
    p = Portfolio(**fixture_portfolio_underweight_risk)
    robot = await mock_robot(p)
    step = await get_position_risks_step(p, robot)
    assert step == SolutionStepEnum.UNDERWEIGHT
    #
    p = Portfolio(**fixture_portfolio_overweight_risk)
    robot = await mock_robot(p)
    step = await get_position_risks_step(p, robot)
    assert step == SolutionStepEnum.OVERWEIGHT


async def test_finish_portfolio_risks(
    fixture_client, fixture_db, fixture_portfolio_underweight_risk
):
    assert fixture_portfolio_underweight_risk["risks"][0]["status"] == 风险点状态.confirmed
    await finish_portfolio_risks()
    portfolio = await get_portfolio_by_id(
        fixture_db, PyObjectId(fixture_portfolio_underweight_risk["_id"])
    )
    assert portfolio.risks[0].status == 风险点状态.resolved


async def test_get_all_risks(
    fixture_client, fixture_db, fixture_portfolio_underweight_risk, mocker
):
    async def fake_timing_strategy_signal(*args):
        return TimingStrategySignalInResponse(
            trade_date=datetime.now().date(),
            market_trend="上升",
            position_rate_advice=[0.2, 0.8],
        )

    mock_timing_strategy_signal = mocker.patch(
        "app.service.risks.risk.timing_strategy_signal",
        side_effect=fake_timing_strategy_signal,
    )
    # show all
    risks = await get_all_risks(
        fixture_db, PyObjectId(fixture_portfolio_underweight_risk["_id"]), True
    )
    assert mock_timing_strategy_signal.called
    assert len(risks) == 1
    assert risks[0].position_advice == [0.2, 0.8]
    #
    risks = await get_all_risks(
        fixture_db, PyObjectId(fixture_portfolio_underweight_risk["_id"]), False
    )
    assert mock_timing_strategy_signal.called
    assert len(risks) == 0


async def test_ignore_abnormal_risks(
    fixture_client,
    fixture_db,
    fixture_portfolio_sci_risk,
    fixture_portfolio_underweight_risk,
):
    # 仓位风险
    await ignore_abnormal_risks(
        fixture_db, Portfolio(**fixture_portfolio_underweight_risk), []
    )
    portfolio = await get_portfolio_by_id(
        fixture_db, PyObjectId(fixture_portfolio_underweight_risk["_id"])
    )
    assert portfolio.risks[0].status == 风险点状态.ignored
    # 个股风险
    # 1.持仓为空
    await ignore_abnormal_risks(fixture_db, Portfolio(**fixture_portfolio_sci_risk), [])
    portfolio = await get_portfolio_by_id(
        fixture_db, PyObjectId(fixture_portfolio_sci_risk["_id"])
    )
    assert len(portfolio.risks) == 3
    assert len([x for x in portfolio.risks if x.status == 风险点状态.ignored]) == 3
    # 2.过滤持仓量为0的股票
    stocks = [
        FundAccountPositionInDB(
            fund_id="",
            symbol="600100",
            exchange=Exchange.CNSESH,
            volume=0,
            available_volume=0,
            cost=100,
        )
    ]
    await ignore_abnormal_risks(
        fixture_db, Portfolio(**fixture_portfolio_sci_risk), stocks
    )
    portfolio = await get_portfolio_by_id(
        fixture_db, PyObjectId(fixture_portfolio_sci_risk["_id"])
    )
    assert len(portfolio.risks) == 3
    assert len([x for x in portfolio.risks if x.status == 风险点状态.ignored]) == 3
    # 3.过滤可用为0的股票
    stocks = [
        FundAccountPositionInDB(
            fund_id="",
            symbol="600100",
            exchange=Exchange.CNSESH,
            volume=100,
            available_volume=0,
            cost=100,
        )
    ]
    await ignore_abnormal_risks(
        fixture_db, Portfolio(**fixture_portfolio_sci_risk), stocks
    )
    portfolio = await get_portfolio_by_id(
        fixture_db, PyObjectId(fixture_portfolio_sci_risk["_id"])
    )
    assert len(portfolio.risks) == 3
    # 4.部分持仓
    stocks = [
        FundAccountPositionInDB(
            fund_id="",
            symbol="600100",
            exchange=Exchange.CNSESH,
            volume=100,
            available_volume=100,
            cost=100,
        )
    ]
    await ignore_abnormal_risks(
        fixture_db, Portfolio(**fixture_portfolio_sci_risk), stocks
    )
    portfolio = await get_portfolio_by_id(
        fixture_db, PyObjectId(fixture_portfolio_sci_risk["_id"])
    )
    assert len(portfolio.risks) == 3
    assert len([x for x in portfolio.risks if x.status == 风险点状态.ignored]) == 2
