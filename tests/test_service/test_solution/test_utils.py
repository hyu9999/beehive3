from collections import Set
from copy import deepcopy
from functools import partial

import pytest
from bson import Decimal128
from bson import ObjectId
from pytest import mark

from app.enums.log import 买卖方向
from app.enums.portfolio import 风险点状态, 风险类型
from app.models.base.portfolio import 风险点信息
from app.models.portfolio import Portfolio
from app.service.risks.utils import get_exchange_from_signal, risk_type_from_signal
from app.service.solutions.utils import build_signal_index, build_risk_set, update_account_info, get_robot
from tests.consts.risks import risks_const
from tests.consts.solution import position_list, fund_asset, solution_order_list
from tests.mocks.robot import MockRobot

pytestmark = mark.asyncio


@mark.parametrize(
    "signal",
    [
        {"SYMBOL": "600179", "MARKET": "CNSESH", "STKEFFEFT": 1000, "TDATE": "20210425", "SIGNAL": 1, "TPRICE": 10, "OPERATOR": "2222"},
        {"SYMBOL": "600179", "MARKET": "CNSESH", "STKEFFEFT": 1000, "TDATE": "20210425", "SIGNAL": 1, "TPRICE": 10, "OPERATOR": "st0001"},
    ],
)
async def test_build_signal_index(signal):
    data = await build_signal_index(signal)
    if signal["OPERATOR"] == "st0001":
        assert data == (risk_type_from_signal(signal), signal["SYMBOL"], await get_exchange_from_signal(signal))
    else:
        assert data is None


@mark.parametrize("solution_order", solution_order_list)
async def test_update_account_info(solution_order):
    response = await update_account_info([solution_order], fund_asset, deepcopy(position_list))
    if solution_order.operator == 买卖方向.buy and solution_order.price != -1:
        assert response == (Decimal128("999000"), Decimal128("1000.00"))
    else:
        assert response == (Decimal128("1000000"), Decimal128("0.00"))


@mark.parametrize("risk", risks_const)
async def test_build_risk_set(risk):
    # 个股风险
    if risk["risk_type"] != 风险类型.clearance_line:
        risk_obj = 风险点信息(**risk)
        risk_set = await build_risk_set([risk_obj])
        assert isinstance(risk_set, Set)
        if risk["risk_type"] == 风险类型.overweight:
            assert (risk_obj.risk_type,) in risk_set
        else:
            assert (risk_obj.risk_type, risk_obj.symbol, risk_obj.exchange) in risk_set
    else:
        # 其他风险
        with pytest.raises(RuntimeError) as exc_info:
            await build_risk_set([风险点信息(**risk)])
            assert exc_info.type is RuntimeError


async def test_get_robot(fixture_portfolio, mocker):
    portfolio = Portfolio(**fixture_portfolio)

    async def fake_account_robot_factory(*args):
        return partial(MockRobot)

    mocker.patch("app.service.solutions.utils.Robot", side_effect=MockRobot)
    mock_account_robot_factory = mocker.patch("app.service.solutions.utils.account_robot_factory", side_effect=fake_account_robot_factory)
    response = await get_robot(portfolio, fund_asset, deepcopy(position_list), [solution_order_list[0]])
    assert mock_account_robot_factory.called
    assert isinstance(response, MockRobot)
