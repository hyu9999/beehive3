import pytest

from app.schema.order import OrderInResponse
from app.service.orders.order import update_from_trade_sys, update_order_stock_name
from tests.consts.order import order_base_data, order_in_db_data
from tests.test_helper import get_random_str

pytestmark = pytest.mark.asyncio


async def test_update_order_stock_name(initialized_app):
    rv = await update_order_stock_name([order_base_data])
    assert rv[0]["symbol_name"]


async def test_update_from_trade_sys():
    order = OrderInResponse(**order_in_db_data)
    data = {
        "order_status": "1",
        "trade_volume": 1000,
        "trade_price": 10,
        "symbol_name": get_random_str(),
    }
    order = await update_from_trade_sys(order, data)
    assert order.symbol_name == data["symbol_name"]
