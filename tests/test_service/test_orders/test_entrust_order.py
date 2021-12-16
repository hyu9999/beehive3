from copy import deepcopy
from typing import Optional

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.order import create_order, delete_order_many, get_orders
from app.enums.order import 订单状态
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.schema.order import OrderInCreate
from app.service.orders.entrust_order import (
    cancel_in_progress_orders,
    get_entrust_orders,
    get_entrust_orders_recent_by_fund_id,
    get_recent_entrust_orders,
    get_task_orders,
)
from tests.consts.order import order_in_db_data
from tests.test_helper import get_random_str

pytestmark = pytest.mark.asyncio


async def create_orders(
    conn: AsyncIOMotorClient,
    fund_id: Optional[str] = None,
    portfolio_id: Optional[PyObjectId] = None,
) -> None:
    order_data = deepcopy(order_in_db_data)
    for status in 订单状态:
        order = OrderInCreate(**order_data)
        if fund_id is not None:
            order.fund_id = fund_id
        if portfolio_id is not None:
            order.portfolio = portfolio_id
        order.status = status
        await create_order(conn, order)


async def test_get_task_orders(
    fixture_db,
):
    await delete_order_many(fixture_db, {})
    await create_orders(fixture_db)
    rv = await get_task_orders()
    assert len(rv[0]["orders"]) == 1


async def test_cancel_in_progress_orders(
    fixture_db,
):
    await delete_order_many(fixture_db, {})
    await create_orders(fixture_db)
    await cancel_in_progress_orders()
    orders = await get_orders(fixture_db, {})
    assert not any([order.status == 订单状态.in_progress for order in orders])


async def test_close_order(fixture_db, mocker):
    mock_fast_tdate = mocker.patch(
        "app.service.orders.entrust_order.FastTdate",
    )
    mock_fast_tdate.is_tdate.return_value = True
    await delete_order_many(fixture_db, {})
    await create_orders(fixture_db)


async def test_get_entrust_orders_recent_by_fund_id(fixture_db):
    fund_id = get_random_str()
    await delete_order_many(fixture_db, {})
    await create_orders(fixture_db, fund_id=fund_id)
    rv = await get_entrust_orders_recent_by_fund_id(fund_id)
    assert rv


async def test_get_entrust_orders(portfolio_in_db: Portfolio):
    tdate = "20210427"
    assert await get_entrust_orders(portfolio_in_db, tdate, tdate, 1)


async def test_get_recent_entrust_orders(
    fixture_db,
    portfolio_in_db,
):
    rv = await get_recent_entrust_orders(fixture_db, portfolio_in_db, 1)
    assert rv
