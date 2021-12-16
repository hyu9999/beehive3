import json
from datetime import datetime, time

import pytest

from app.global_var import G
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.schema.portfolio import PortfolioInResponse
from app.service.orders.order_trade import OrderTrade
from tests.consts.order import order_in_db_data

pytestmark = pytest.mark.asyncio


def test_is_trade_time(mocker):
    mock_is_closed = mocker.patch(
        "app.service.orders.order_trade.FastTdate.is_closed", return_value=False
    )
    mock_datetime = mocker.patch("app.service.orders.order_trade.datetime")
    mock_datetime.now.return_value.time.return_value = time(13)
    rv = OrderTrade.is_trade_time()
    assert rv
    mock_is_closed.assert_called()


def test_check_trade_time(mocker):
    mock_is_closed = mocker.patch(
        "app.service.orders.order_trade.FastTdate.is_closed", return_value=False
    )
    mock_datetime = mocker.patch("app.service.orders.order_trade.datetime")
    mock_datetime.now.return_value = datetime(2021, 5, 1, 14)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    OrderTrade.check_trade_time()
    mock_is_closed.assert_called()


@pytest.mark.parametrize("task_id", [None, "1"])
async def test_insert_to_monitor_pool(portfolio_in_db: Portfolio, task_id):
    order = Order(**order_in_db_data)
    portfolio = PortfolioInResponse(**portfolio_in_db.dict())
    await OrderTrade.insert_to_monitor_pool(portfolio, [order], task_id)
    if task_id is None:
        rv = await G.entrust_redis.hget(str(portfolio.id), order.order_id)
        assert rv == order.status.value
    else:
        rv = await G.entrust_redis.hget(str(portfolio.id), "task")
        rv = json.loads(rv)
        assert rv["task_id"] == task_id
