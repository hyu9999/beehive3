from copy import deepcopy
from datetime import datetime

import pytest

from app.crud.order import delete_order_many, get_order_by_id, get_orders
from app.enums.order import 订单状态
from app.global_var import G
from app.models.base.order import 股票订单基本信息
from app.models.portfolio import Portfolio
from app.schema.portfolio import PortfolioInResponse
from app.service.orders.entrust_order import get_task_orders
from app.service.orders.order_trade_put import PutOrder, entrust_orders
from tests.consts.order import order_base_data, order_in_db_data
from tests.test_service.test_orders.test_entrust_order import create_orders

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("price", [10, -1])
async def test_put_order_to_trade_sys(portfolio_in_db: Portfolio, price):
    portfolio = PortfolioInResponse(**portfolio_in_db.dict())
    order = deepcopy(order_in_db_data)
    order["price"] = price
    rv = await PutOrder.put_order_to_trade_sys(order, portfolio)
    assert rv.flag


async def test_put_order(mocker, fixture_db, portfolio_in_db: Portfolio):
    await delete_order_many(fixture_db, {})
    mock_check_trade_time = mocker.patch(
        "app.service.orders.order_trade_put.OrderTrade.check_trade_time", auto_spec=True
    )
    await create_orders(fixture_db, portfolio_id=portfolio_in_db.id)
    task_order = await get_task_orders()
    orders = task_order[0]["orders"]
    await PutOrder.put_order()
    mock_check_trade_time.assert_called_once()
    rv = await G.entrust_redis.hgetall(str(portfolio_in_db.id))
    assert len(rv) == len(orders)
    assert list(rv.values())[0] == 订单状态.in_progress.value
    for order in orders:
        order_in_db = await get_order_by_id(fixture_db, order["_id"])
        assert order_in_db.status == 订单状态.in_progress.value


@pytest.mark.parametrize("is_task", [True, False])
async def test_entrust_orders(fixture_db, portfolio_with_user, mocker, is_task):
    await delete_order_many(fixture_db, {})
    portfolio, user = portfolio_with_user
    portfolio = PortfolioInResponse(**portfolio.dict())
    order = 股票订单基本信息(**order_base_data)
    mock_is_tdate = mocker.patch(
        "app.service.orders.order_trade_put.FastTdate.is_tdate", return_value=True
    )
    mock_datetime = mocker.patch("app.service.orders.order_trade_put.datetime")
    mock_datetime.now.return_value = datetime(2021, 5, 1, 14)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    mocker.patch(
        "app.service.orders.order_trade_put.OrderTrade.check_trade_time", auto_spec=True
    )
    rv = await entrust_orders(fixture_db, user, portfolio, [order], is_task)
    if not is_task:
        mock_is_tdate.assert_called()
        mock_datetime.now.assert_called()
    assert rv.status
    order_in_db = await get_orders(fixture_db, {"portfolio": portfolio.id})
    assert order_in_db[0].status == 订单状态.in_progress.value
