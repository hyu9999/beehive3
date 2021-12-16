import copy
from datetime import datetime

import pytest

from app.crud.order import create_order, delete_order_many
from app.crud.portfolio import create_portfolio
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.schema.order import OrderInCreate
from tests.consts.order import order_base_data, order_in_create_data
from tests.test_helper import get_header, get_random_str

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def order_in_db(fixture_db):
    order = OrderInCreate(**order_in_create_data)
    return await create_order(fixture_db, order)


async def test_user_can_create_order(authorized_client):
    response = await authorized_client.post(
        "orders", json={"order": order_in_create_data}
    )
    assert response.json()["order_id"] == order_in_create_data["order_id"]


async def test_user_can_delete_order(
    client, fixture_settings, logged_in_root_user, order_in_db: Order
):
    client.headers = get_header(fixture_settings, logged_in_root_user)
    response = await client.delete(f"orders/{order_in_db.id}")
    assert response.json()["result"] == "success"


async def test_user_can_update_order_view(authorized_client, order_in_db: Order):
    response = await authorized_client.put(
        f"orders/{order_in_db.id}", json={"order": order_base_data}
    )
    assert response.json()["matched_count"] == 1
    assert response.json()["modified_count"] == 1


async def test_user_can_partial_update_order_view(
    authorized_client, order_in_db: Order
):
    response = await authorized_client.patch(
        f"orders/{order_in_db.id}", json={"order": order_base_data}
    )
    assert response.json()["matched_count"] == 1
    assert response.json()["modified_count"] == 1


async def test_user_can_get_orders(authorized_client, order_in_db: Order):
    response = await authorized_client.get(f"orders/list")
    assert response.json()


async def test_user_can_get_order(authorized_client, order_in_db: Order):
    response = await authorized_client.get(f"orders/{order_in_db.id}")
    assert response.json()["order_id"] == str(order_in_db.order_id)


async def test_user_can_create_entrust_order(
    client,
    fixture_db,
    portfolio_data_in_db,
    logined_vip_user,
    fixture_settings,
    mocker,
):
    await delete_order_many(fixture_db, {})
    portfolio_data_in_db = copy.deepcopy(portfolio_data_in_db)
    portfolio_data_in_db["username"] = logined_vip_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    client.headers = get_header(fixture_settings, logined_vip_user)
    mock_is_tdate = mocker.patch(
        "app.service.orders.order_trade_put.FastTdate.is_tdate", return_value=True
    )
    mock_datetime = mocker.patch("app.service.orders.order_trade_put.datetime")
    mock_datetime.now.return_value = datetime(2021, 5, 1, 14)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    mocker.patch(
        "app.service.orders.order_trade_put.OrderTrade.check_trade_time", auto_spec=True
    )
    order_json = copy.deepcopy(order_base_data)
    order_json["order_id"] = portfolio.fund_account[0].fundid
    response = await client.post(
        f"orders/{portfolio.id}/entrust_orders",
        json={"orders": [order_base_data]},
    )
    mock_is_tdate.assert_called()
    assert response.json()["status"]


@pytest.mark.parametrize("op_flag", [1, 2, 3])
async def test_user_can_get_entrust_order(
    authorized_client, op_flag, portfolio_in_db: Portfolio
):
    response = await authorized_client.get(
        f"orders/{portfolio_in_db.id}/entrust_orders?op_flag={op_flag}"
    )
    assert response.json()


async def test_user_can_delete_entrust_order(
    authorized_client,
    portfolio_data_in_db,
    logined_vip_user,
    client,
    fixture_db,
    fixture_settings,
    order_in_db: Order,
):
    portfolio_data_in_db = copy.deepcopy(portfolio_data_in_db)
    portfolio_data_in_db["username"] = logined_vip_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    client.headers = get_header(fixture_settings, logined_vip_user)
    response = await authorized_client.delete(
        f"orders/{portfolio.id}/entrust_orders/1?db_id={order_in_db.id}"
    )
    assert response.json()["status"]


async def test_user_can_get_task_order(fixture_db, authorized_client):
    order_in_create = OrderInCreate(**order_in_create_data)
    order_in_create.task = get_random_str()
    order = await create_order(fixture_db, order_in_create)
    response = await authorized_client.get(f"orders/task_orders/{order.task}")
    assert response.json()["id"] == order.task


async def test_user_can_get_task_order_list(
    fixture_db, client, logined_vip_user, fixture_settings
):
    order_in_create = OrderInCreate(**order_in_create_data)
    order_in_create.status = "1"
    order_in_create.username = logined_vip_user["user"]["username"]
    client.headers = get_header(fixture_settings, logined_vip_user)
    order = await create_order(fixture_db, order_in_create)
    response = await client.get(f"orders/task_orders/")
    assert response.json()[0]["id"] == order.task
