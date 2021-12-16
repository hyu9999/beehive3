import pytest

from app.crud.order import create_order
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.schema.order import OrderInCreate
from app.schema.portfolio import PortfolioInResponse
from app.service.orders.order_trade import OrderTrade
from app.service.orders.order_trade_check import CheckOrder
from tests.consts.mock_pt_response_data import PT_ORDER_GET_RESPONSE
from tests.consts.order import order_in_db_data
from tests.test_helper import get_random_str

pytestmark = pytest.mark.asyncio


async def test_check_order(portfolio_in_db: Portfolio, logged_in_free_user, fixture_db):
    portfolio = PortfolioInResponse(**portfolio_in_db.dict())
    order = Order(**order_in_db_data)
    order.username = logged_in_free_user["user"]["username"]
    order.order_id = PT_ORDER_GET_RESPONSE[0]["entrust_id"]
    await create_order(fixture_db, OrderInCreate(**order.dict()))
    task_id = get_random_str()
    await OrderTrade.insert_to_monitor_pool(portfolio, [order], task_id)
    await CheckOrder.check_order()
