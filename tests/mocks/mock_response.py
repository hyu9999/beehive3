import re
from copy import deepcopy
from urllib.parse import unquote, urljoin

import pytest
from aioresponses import CallbackResult, aioresponses

from tests.consts.mock_disc_response_data import (
    DISC_LOGIN_RESPONSE,
    DISC_THREAD_CREATE_RESPONSE,
    DISC_USER_GET_RESPONSE,
    DISC_USER_PATCH_RESPONSE,
)
from tests.consts.mock_pt_response_data import (
    PT_ORDER_DELETE_RESPONSE,
    PT_ORDER_GET_RESPONSE,
    PT_ORDER_POST_RESPONSE,
    PT_POSITION_GET_RESPONSE,
    PT_REGISTER_RESPONSE,
    PT_STATEMENT_GET_RESPONSE,
    PT_USER_GET_RESPONSE,
)


def pt_register_callback(_, **kwargs):
    json = deepcopy(PT_REGISTER_RESPONSE)
    capital = kwargs["json"].get("capital")
    desc = kwargs["json"].get("desc")
    if capital is not None:
        json["capital"] = capital
    if desc is not None:
        json["desc"] = desc
    return CallbackResult(status=200, payload=json)


def pt_user_get_callback(url, **kwargs):
    json = deepcopy(PT_USER_GET_RESPONSE)
    json["_id"] = url.path.split("/")[-1]
    return CallbackResult(status=200, payload=json)


def pt_order_post_callback(_, **kwargs):
    json = deepcopy(PT_ORDER_POST_RESPONSE)
    json["symbol"] = kwargs["json"]["symbol"]
    json["exchange"] = kwargs["json"]["exchange"]
    return CallbackResult(status=200, payload=json)


def pt_order_get_callback(url, **kwargs):
    json = deepcopy(PT_ORDER_GET_RESPONSE)
    op_flag = url.query.get("status")
    if op_flag is not None:
        for j in json:
            j["status"] = unquote(op_flag)
    return CallbackResult(status=200, payload=json)


def pt_statement_get_callback(url, **kwargs):
    json = deepcopy(PT_STATEMENT_GET_RESPONSE)
    user_id = kwargs["headers"]["Authorization"].split()[-1]
    for j in json:
        j["user"] = user_id
    return CallbackResult(status=200, payload=json)


@pytest.fixture(autouse=True, scope="session")
def mock_response(fixture_settings):
    disc_base_url = fixture_settings.discuzq.base_url
    pt_base_url = fixture_settings.trade_url
    with aioresponses() as m:
        # 社区
        # 登录
        m.post(
            urljoin(disc_base_url, "api/login"),
            status=200,
            payload=DISC_LOGIN_RESPONSE,
            repeat=True,
        )

        # 获取用户
        disc_user_url_pattern = re.compile(
            fr"^{urljoin(disc_base_url, 'api/users')}/\d$"
        )
        m.get(
            disc_user_url_pattern,
            status=200,
            payload=DISC_USER_GET_RESPONSE,
            repeat=True,
        )

        # 查询用户
        disc_user_filter_url_pattern = re.compile(
            fr"^{urljoin(disc_base_url, 'api/users')}\?filter.*?$"
        )
        m.get(
            disc_user_filter_url_pattern,
            status=200,
            payload=DISC_USER_GET_RESPONSE,
            repeat=True,
        )

        # 更新用户
        m.patch(
            disc_user_url_pattern,
            status=200,
            payload=DISC_USER_PATCH_RESPONSE,
            repeat=True,
        )

        # 创建帖子
        m.post(
            urljoin(disc_base_url, "api/threads"),
            status=200,
            payload=DISC_THREAD_CREATE_RESPONSE,
            repeat=True,
        )

        # 交易系统
        # 注册
        m.post(
            urljoin(pt_base_url, "auth/register"),
            callback=pt_register_callback,
            repeat=True,
        )

        # 获取用户
        pt_user_url_pattern = re.compile(fr"^{urljoin(pt_base_url, 'users')}/.*$")
        m.get(
            pt_user_url_pattern,
            callback=pt_user_get_callback,
            repeat=True,
        )

        # 获取持仓
        pt_position_url_pattern = re.compile(
            fr"^{urljoin(pt_base_url, 'position')}/.*$"
        )
        m.get(
            pt_position_url_pattern,
            status=200,
            payload=PT_POSITION_GET_RESPONSE,
            repeat=True,
        )

        # 创建订单
        m.post(
            urljoin(pt_base_url, "orders/"),
            callback=pt_order_post_callback,
            repeat=True,
        )

        # 取消委托单
        pt_order_url_pattern = re.compile(fr"^{urljoin(pt_base_url, 'orders')}/.*$")
        m.delete(
            pt_order_url_pattern,
            status=200,
            payload=PT_ORDER_DELETE_RESPONSE,
            repeat=True,
        )

        # 查询订单列表
        m.get(
            pt_order_url_pattern,
            callback=pt_order_get_callback,
            repeat=True,
        )

        # 查询交割单列表
        pt_statement_url_pattern = re.compile(
            fr"^{urljoin(pt_base_url, 'statement')}/.*$"
        )
        m.get(
            pt_statement_url_pattern,
            callback=pt_statement_get_callback,
            repeat=True,
        )
        yield m
