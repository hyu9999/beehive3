from contextlib import nullcontext
from datetime import datetime

import pytest
from yarl import URL

from app.outer_sys.trade_system.pt.mapper import INPUT, INTERFACE
from app.outer_sys.trade_system.pt.output_tuple import (
    ACCOUNT,
    ASSET,
    ORDER,
    ORDER_RECORD,
    POSITION,
    REGISTER,
    STATEMENT,
)
from app.outer_sys.trade_system.pt.pt_trade_adaptor import PTAdaptor
from tests.consts.mock_pt_response_data import (
    PT_ORDER_DELETE_RESPONSE,
    PT_ORDER_GET_RESPONSE,
    PT_ORDER_POST_RESPONSE,
    PT_POSITION_GET_RESPONSE,
    PT_REGISTER_RESPONSE,
    PT_STATEMENT_GET_RESPONSE,
    PT_USER_GET_RESPONSE,
)
from tests.test_helper import get_random_str

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def pt_adaptor(fixture_settings):
    pt_adaptor = PTAdaptor(fixture_settings.trade_url)
    return pt_adaptor


@pytest.mark.parametrize(
    "path, name, query, result",
    [
        ("users/", "", None, "/users/"),
        ("users/", "5f8163f4ef78c0513b8724d1", None, "/users/5f8163f4ef78c0513b8724d1"),
        (
            "orders/",
            "",
            {"status": "已撤销", "start_date": "1967-06-28"},
            "/orders/?status=已撤销&start_date=1967-06-28",
        ),
        (
            "orders/",
            "5f8163f4ef78c0513b8724d1",
            {"status": "已撤销"},
            "/orders/5f8163f4ef78c0513b8724d1?status=已撤销",
        ),
    ],
)
def test_make_url(pt_adaptor: PTAdaptor, fixture_settings, path, name, query, result):
    url = pt_adaptor._make_url(path, name, query)
    assert url == URL(f"{fixture_settings.trade_url}{result}")


@pytest.mark.parametrize(
    "login_required, payload, result",
    [
        (
            True,
            {"account_id": "5f8163f4ef78c0513b8724d1"},
            {"Authorization": "Token 5f8163f4ef78c0513b8724d1"},
        ),
        (False, None, None),
    ],
)
def test_make_headers(pt_adaptor: PTAdaptor, login_required, payload, result):
    headers = pt_adaptor._make_headers(login_required, payload)
    assert headers == result


@pytest.mark.parametrize(
    "func_name, data, result",
    [
        ("register_trade_system", PT_REGISTER_RESPONSE, REGISTER),
        ("create_fund_account", PT_REGISTER_RESPONSE, ACCOUNT),
        ("get_fund_account", PT_USER_GET_RESPONSE, ACCOUNT),
        ("get_fund_asset", PT_USER_GET_RESPONSE, ASSET),
        ("get_fund_stock", PT_POSITION_GET_RESPONSE[0], POSITION),
        ("get_today_orders", PT_ORDER_GET_RESPONSE[0], ORDER_RECORD),
        ("get_orders", PT_ORDER_GET_RESPONSE[0], ORDER_RECORD),
        ("get_statement", PT_STATEMENT_GET_RESPONSE[0], STATEMENT),
        ("order_input", PT_ORDER_POST_RESPONSE, ORDER),
    ],
)
def test_out2beehive(pt_adaptor: PTAdaptor, func_name, data, result):
    rv = pt_adaptor.out2beehive(func_name, data)
    for item in result:
        if data.get(item[1]) is not None:
            assert rv[item[0]] == data[item[1]]
        else:
            assert rv[item[0]] == item[2]


def test_beehive2out(pt_adaptor: PTAdaptor):
    for key in INPUT.keys():
        v = get_random_str()
        rv = pt_adaptor.beehive2out(**{key: v})
        assert rv[INPUT[key]] == v


def test_function2path(pt_adaptor: PTAdaptor):
    for k, v in INTERFACE.items():
        rv = pt_adaptor.function2interface(k)
        assert rv == v


@pytest.mark.parametrize(
    "date, result, expected_raises",
    [
        ("20210501", "2021-05-01", nullcontext()),
        ("2021", None, pytest.raises(ValueError)),
    ],
)
def test_beehive_date_to_pt_date(pt_adaptor: PTAdaptor, date, result, expected_raises):
    with expected_raises:
        assert result == pt_adaptor.beehive_date_to_pt_date(date)


@pytest.mark.parametrize(
    "login_required, convert_out",
    [(True, False), (True, True), (False, True), (False, False)],
)
async def test_request_interface(pt_adaptor: PTAdaptor, login_required, convert_out):
    tir = await pt_adaptor.request_interface(
        func_name="get_orders",
        payload={"account_id": "1"},
        login_required=login_required,
        convert_out=convert_out,
    )
    assert tir.flag
    assert tir.data


async def test_register_trade_system(pt_adaptor: PTAdaptor):
    kwargs = {"user_id": get_random_str(), "mobile": "15333333333"}
    tir = await pt_adaptor.register_trade_system(**kwargs)
    assert tir.flag
    assert tir.data["fund_id"] == PT_REGISTER_RESPONSE["_id"]


async def test_create_fund_account(pt_adaptor: PTAdaptor):
    kwargs = {"trade_user_id": get_random_str(), "total_input": 10000}
    tir = await pt_adaptor.create_fund_account(**kwargs)
    assert tir.flag
    assert tir.data["fund_id"] == PT_REGISTER_RESPONSE["_id"]


async def test_bind_fund_account(pt_adaptor: PTAdaptor):
    kwargs = {"trade_user_id": get_random_str(), "total_input": 10000}
    tir = await pt_adaptor.bind_fund_account(**kwargs)
    assert tir.flag
    assert tir.data["fund_id"] == PT_REGISTER_RESPONSE["_id"]


async def test_get_fund_account(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str()}
    tir = await pt_adaptor.get_fund_account(**kwargs)
    assert tir.flag
    assert tir.data["fund_id"] == kwargs["fund_id"]


async def test_get_fund_stock(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str(), "convert_out": False}
    tir = await pt_adaptor.get_fund_stock(**kwargs)
    assert tir.flag
    assert tir.data == PT_POSITION_GET_RESPONSE


async def test_get_fund_asset(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str(), "convert_out": False}
    tir = await pt_adaptor.get_fund_asset(**kwargs)
    assert tir.flag
    assert tir.data["_id"] == kwargs["fund_id"]


async def test_order_input(pt_adaptor: PTAdaptor):
    kwargs = {
        "fund_id": get_random_str(),
        "symbol": get_random_str(),
        "exchange": "SH",
        "order_price": "15.10",
        "order_direction": "buy",
        "order_quantity": 400,
        "order_date": str(datetime.today().date()),
        "order_time": str(datetime.today().time()),
    }
    tir = await pt_adaptor.order_input(**kwargs)
    assert tir.flag
    assert tir.data["order_id"]


async def test_order_cancel(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str(), "order_id": get_random_str()}
    tir = await pt_adaptor.order_cancel(**kwargs)
    assert tir.flag
    assert tir.data == PT_ORDER_DELETE_RESPONSE


async def test_get_today_orders(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str()}
    tir = await pt_adaptor.get_today_orders(**kwargs)
    assert tir.flag
    assert tir.data == PT_ORDER_GET_RESPONSE


async def test_get_orders(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str()}
    tir = await pt_adaptor.get_orders(**kwargs)
    assert tir.flag
    assert tir.data == PT_ORDER_GET_RESPONSE


@pytest.mark.parametrize("op_flag, result", [(1, None), (2, "全部成交"), (3, "未成交")])
async def test_get_order_record(client, pt_adaptor: PTAdaptor, op_flag, result):
    kwargs = {"fund_id": get_random_str(), "op_flag": op_flag}
    tir = await pt_adaptor.get_order_record(**kwargs)
    assert tir.flag
    if op_flag is 1:
        assert len(set([order["order_status_ex"] for order in tir.data])) == 3
    else:
        for order in tir.data:
            assert order["order_status_ex"] == result


async def test_get_statement(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str()}
    tir = await pt_adaptor.get_statement(**kwargs)
    assert tir.flag
    for item in tir.data:
        assert item["fund_id"] == kwargs["fund_id"]


async def test_manual_clear(pt_adaptor: PTAdaptor):
    kwargs = {"fund_id": get_random_str()}
    tir = await pt_adaptor.manual_clear(**kwargs)
    assert tir.flag
    assert tir.data == "清算完成"
