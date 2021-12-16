import copy
from datetime import date, timedelta

from bson import ObjectId
from pytest import fixture, mark

from app.core.errors import CreateQuantityLimit, NoUserError
from app.enums.equipment import 装备分类_3
from app.enums.user import 消息分类, 消息类型
from tests.consts.equipment import screen_test_data
from tests.consts.robots import robot_test_data
from tests.mocks.robot import mock_check_strategy_exist_with_true, mock_check_strategy_exist_with_false
from tests.mocks.topic import mock_get_or_create_disc_user, mock_update_user_signature


@fixture
def unregistered_user(fixture_settings, fixture_db):
    """待注册用户"""
    yield {
        "user": {
            "mobile": "19000000000",
            "email": "user@example.com",
            "password": "string1",
            "username": "test_register_user",
            "nickname": "string",
            "code": fixture_settings.sms.fixed_code,
        }
    }
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.USER].delete_many({"username": {"$regex": "^test"}})


@fixture
def fixture_create_message_data(free_user_data, fixture_settings, fixture_db):
    """消息创建模型数据"""
    yield {
        "title": "test_create_message",
        "content": "test_create_message",
        "category": 消息分类.portfolio,
        "msg_type": 消息类型.signal,
        "username": free_user_data["user"]["username"],
        "data_info": "",
    }
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.USER_MESSAGE].delete_many(
        {"$or": [{"username": {"$regex": "^test"}}, {"title": {"$regex": "^test"}}]}
    )


def test_get_view(fixture_client, fixture_settings, logined_free_user, free_user_headers):
    """获取用户信息"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["username"] == logined_free_user["user"]["username"]
    assert response.json()["mobile"] == logined_free_user["user"]["mobile"]
    # 获取指定用户信息
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user",
        params={"username": logined_free_user["user"]["username"]},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["username"] == logined_free_user["user"]["username"]
    assert response.json()["mobile"] == logined_free_user["user"]["mobile"]
    # 查询用户不存在
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user",
        params={"username": "test_not_found"},
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert NoUserError.message in response.text


def test_check_exist_get_view(fixture_client, fixture_settings, logined_free_user, free_user_headers):
    """检查账户是否存在"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/check_exist/",
        params={"username": logined_free_user["user"]["username"]},
    )
    assert response.status_code == 200
    assert "success" in response.text
    # 查询账户不存在
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/check_exist/",
        params={"username": "test_not_exist"},
    )
    assert response.status_code == 200
    assert "failed" in response.text


@mark.skip
def test_register_view(fixture_client, fixture_settings, unregistered_user):
    """注册用户"""
    # close disc
    fixture_settings.discuzq.switch = False
    response = fixture_client.post(f"{fixture_settings.url_prefix}/user/register", json=unregistered_user)
    assert response.status_code == 201
    assert "success" in response.text
    # 注册账户已存在
    response = fixture_client.post(f"{fixture_settings.url_prefix}/user/register", json=unregistered_user)
    assert response.status_code == 400
    assert "您输入的帐号已被注册" in response.text
    unregistered_user2 = copy.deepcopy(unregistered_user)
    unregistered_user2["user"]["username"] = "test_register_user2"
    response = fixture_client.post(f"{fixture_settings.url_prefix}/user/register", json=unregistered_user2)
    assert response.status_code == 400
    assert "您输入的邮箱号已被注册" in response.text
    unregistered_user2["user"]["email"] = "19000000001@example.com"
    response = fixture_client.post(f"{fixture_settings.url_prefix}/user/register", json=unregistered_user2)
    assert response.status_code == 400
    assert "您输入的手机号已被注册" in response.text


def test_create_view(
    fixture_client,
    fixture_settings,
    unregistered_user,
    free_user_headers,
    root_user_headers,
):
    """创建用户"""
    unregistered_user["user"].pop("nickname")
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user",
        json=unregistered_user,
        headers=root_user_headers,
    )
    assert response.status_code == 201
    assert "success" in response.text
    # 权限不足
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user",
        json=unregistered_user,
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "权限不足" in response.text


def test_delete_view(
    fixture_client,
    fixture_settings,
    unregistered_user,
    free_user_headers,
    root_user_headers,
):
    """删除用户"""
    response = fixture_client.post(f"{fixture_settings.url_prefix}/user/register", json=unregistered_user)
    assert response.status_code == 201
    assert "token" in response.text
    # 权限不足
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/user/{unregistered_user['user']['username']}",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "权限不足" in response.text
    # 用户不存在
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/user/{'test_not_exist'}",
        headers=root_user_headers,
    )
    assert response.status_code == 400
    assert "用户不存在或者已经删除" in response.text
    # 正例
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/user/{unregistered_user['user']['username']}",
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text


def test_update_view(fixture_client, fixture_settings, free_user_headers, logined_free_user):
    """更新用户信息"""
    update_user_data = logined_free_user
    update_user_data["user"]["nickname"] = "free_nickname"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user",
        json=update_user_data,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["nickname"] == "free_nickname"


def test_forget_pwd_view(fixture_client, fixture_settings, free_user_headers, logined_free_user):
    """忘记密码"""
    update_user_data = {
        "user": {
            "mobile": logined_free_user["user"]["mobile"],
            "password": "qwer1234",
        }
    }
    response = fixture_client.put("user/forget", json=update_user_data, headers=free_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    # 手机未注册
    update_user_data["user"]["mobile"] = 19912341234
    response = fixture_client.put("user/forget", json=update_user_data, headers=free_user_headers)
    assert response.status_code == 400
    assert f"您输入的手机号'{update_user_data['user']['mobile']}'尚未注册，请先注册！" in response.text


def test_update_pwd_view(fixture_client, fixture_settings, free_user_headers, logined_free_user):
    """修改密码"""
    update_user_data = {
        "user": {
            "mobile": logined_free_user["user"]["mobile"],
            "password": "qwer1234",
        }
    }
    response = fixture_client.put("user/password", json=update_user_data, headers=free_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    # 手机未注册
    update_user_data["user"]["mobile"] = 19912341234
    response = fixture_client.put("user/password", json=update_user_data, headers=free_user_headers)
    assert response.status_code == 400
    assert f"权限不足，请联系客服或者管理员" in response.text


def test_refresh_token_get_view(fixture_client, fixture_settings, free_user_headers, logined_free_user):
    """刷新token"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user/refresh", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["token"] is not None


def test_subscribe_equipment_action_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    vip_user_headers,
    fixture_off_line_risk_equipment,
):
    """订阅装备"""
    # 订阅装备不存在
    not_found_sid = "01180706ntfd01"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{not_found_sid}/equipments",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert f"装备不存在" in response.text
    # 订阅自己创建的装备
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{screen_test_data['标识符']}/equipments",
        headers=vip_user_headers,
    )
    assert response.status_code == 400
    assert f"无法订阅自己创建的装备" in response.text
    # 正例，查看订阅结果
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{screen_test_data['标识符']}/equipments",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["equipment"]["subscribe_info"]["fans_num"] == 1
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["equipment"]["subscribe_info"]["focus_num"] == 1
    # 重复订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{screen_test_data['标识符']}/equipments",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    # 未上线装备无法订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_off_line_risk_equipment['标识符']}/equipments",
        headers=vip_user_headers,
    )
    assert response.status_code == 400
    assert "该装备无法被订阅" in response.text
    # 取消订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{screen_test_data['标识符']}/equipments",
        params={"is_subscribe": False},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=free_user_headers)
    assert response.json()["equipment"]["subscribe_info"]["fans_num"] == 0
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["equipment"]["subscribe_info"]["focus_num"] == 0
    # 重复取消
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{screen_test_data['标识符']}/equipments",
        params={"is_subscribe": False},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text


def test_subscribe_robot_action_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    vip_user_headers,
    fixture_offline_robot,
):
    """订阅机器人"""
    # 订阅机器人不存在
    not_found_sid = "10000000ntfd01"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{not_found_sid}/robots",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert f"机器人不存在" in response.text
    # 订阅自己创建的机器人
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{robot_test_data['标识符']}/robots",
        headers=vip_user_headers,
    )
    assert response.status_code == 400
    assert f"无法订阅自己创建的机器人" in response.text
    # 正例
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{robot_test_data['标识符']}/robots",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=free_user_headers)
    assert response.json()["robot"]["subscribe_info"]["fans_num"] == 0
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["robot"]["subscribe_info"]["focus_num"] == 1
    # 重复订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{robot_test_data['标识符']}/robots",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    # 未上线机器人无法订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_offline_robot['标识符']}/robots",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "该机器人无法被订阅" in response.text
    # 取消订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{robot_test_data['标识符']}/robots",
        params={"is_subscribe": False},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=free_user_headers)
    assert response.json()["robot"]["subscribe_info"]["fans_num"] == 0
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["robot"]["subscribe_info"]["focus_num"] == 0
    # 重复取消
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{robot_test_data['标识符']}/robots",
        params={"is_subscribe": False},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text


def test_subscribe_portfolio_action_view(
    fixture_client,
    fixture_settings,
    vip_user_headers,
    root_user_headers,
    fixture_portfolio,
    fixture_off_line_portfolio,
):
    """订阅组合"""
    # 订阅组合不存在
    not_found_sid = ObjectId()
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{not_found_sid}/portfolios",
        headers=vip_user_headers,
    )
    assert response.status_code == 400
    assert f"组合不存在" in response.text
    # 订阅自己创建的组合
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_portfolio['_id']}/portfolios",
        headers=vip_user_headers,
    )
    assert response.status_code == 400
    assert f"无法订阅自己创建的组合" in response.text
    # 正例
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_portfolio['_id']}/portfolios",
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=root_user_headers)
    assert response.json()["portfolio"]["subscribe_info"]["fans_num"] == 0
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["portfolio"]["subscribe_info"]["focus_num"] == 1
    # 重复订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_portfolio['_id']}/portfolios",
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    # 关闭的组合无法订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_off_line_portfolio['_id']}/portfolios",
        headers=root_user_headers,
    )
    assert response.status_code == 400
    assert "该组合无法被订阅" in response.text
    # 取消订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_portfolio['_id']}/portfolios",
        params={"is_subscribe": False},
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=root_user_headers)
    assert response.json()["portfolio"]["subscribe_info"]["fans_num"] == 0
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["portfolio"]["subscribe_info"]["focus_num"] == 0
    # 重复取消
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_portfolio['_id']}/portfolios",
        params={"is_subscribe": False},
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text


def test_subscribe_portfolio_exist_get_view(fixture_client, fixture_settings, vip_user_headers, free_user_headers, fixture_portfolio):
    """是否订阅组合"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/subscribe/portfolio/{fixture_portfolio['_id']}/exist",
        headers=vip_user_headers,
    )
    assert response.status_code == 200
    assert "false" in response.text
    # 组合已订阅
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/subscribe/{fixture_portfolio['_id']}/portfolios",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/subscribe/portfolio/{fixture_portfolio['_id']}/exist",
        headers=vip_user_headers,
    )
    assert response.status_code == 200
    assert "false" in response.text


def test_message_create_view(
    fixture_client,
    fixture_settings,
    root_user_headers,
    free_user_headers,
    free_user_data,
    fixture_create_message_data,
):
    """创建消息"""
    # 消息接收人不存在
    message_data = fixture_create_message_data
    message_data["username"] = "test_not_found"
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user/message",
        json=message_data,
        headers=root_user_headers,
    )
    assert response.status_code == 400
    assert "消息接收人不存在" in response.text
    # 非公告消息
    message_data["username"] = free_user_data["user"]["username"]
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user/message",
        json=message_data,
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text
    # 公告消息
    message_data["msg_type"] = 消息类型.notice
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user/message",
        json=message_data,
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text


def test_message_list_view(
    fixture_client,
    fixture_settings,
    root_user_headers,
    free_user_headers,
    free_user_data,
    fixture_create_message_data,
):
    """获取用户消息列表"""
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user/message",
        json=fixture_create_message_data,
        headers=root_user_headers,
    )
    assert response.status_code == 200
    start_date = date.today()
    end_date = start_date + timedelta(days=1)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/messages",
        params={"start_date": start_date, "end_date": end_date},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["数据"] is not None
    assert response.json()["数据"][0]["content"] == fixture_create_message_data["content"]
    # 已读
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/messages",
        params={"start_date": start_date, "end_date": end_date, "is_read": True},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["数据"] == []
    # 未读
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/messages",
        params={"start_date": start_date, "end_date": end_date, "is_read": False},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["数据"] is not None
    assert response.json()["数据"][0]["content"] == fixture_create_message_data["content"]


def test_message_put_view(
    fixture_client,
    fixture_settings,
    root_user_headers,
    free_user_headers,
    free_user_data,
    fixture_create_message_data,
):
    """已读用户消息"""
    # 写入数据
    start_date = date.today()
    end_date = start_date + timedelta(days=1)
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user/message",
        json=fixture_create_message_data,
        headers=root_user_headers,
    )
    assert response.status_code == 200
    # 已读全部
    response = fixture_client.put(f"{fixture_settings.url_prefix}/user/message", headers=free_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    # 写入数据
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/user/message",
        json=fixture_create_message_data,
        headers=root_user_headers,
    )
    assert response.status_code == 200
    # 查询写入数据的id
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/messages",
        params={"start_date": start_date, "end_date": end_date},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    id = response.json()["数据"][0]["_id"]
    # 已读单条
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/message",
        params={"id": id},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text


def test_verify_vip_code_action_view(fixture_client, fixture_settings, free_user_headers, root_user_headers):
    """验证vip邀请码"""
    code = fixture_settings.vip_code + "a"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/verify/vcode",
        params={"code": code},
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "邀请码错误" in response.text
    # 非免费用户无法升级vip
    vcode = fixture_settings.vip_code
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/verify/vcode",
        params={"code": vcode},
        headers=root_user_headers,
    )
    assert response.status_code == 400
    assert "非免费用户无法升级vip" in response.text
    # 正例
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/user/verify/vcode",
        params={"code": vcode},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "success" in response.text


@mark.skip
def test_portfolio_targets_get_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    free_user_data,
    fixture_portfolio,
):
    """获取用户组合指标配置列表"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/user/portfolio_targets",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["portfolio"]["name"] == fixture_portfolio["name"]
    assert response.json()[0]["user"]["username"] == free_user_data["user"]["username"]


@mark.parametrize(
    "category, 装备分类, user_type",
    [
        (消息分类.equipment, 装备分类_3.选股, "免费用户"),
        (消息分类.equipment, 装备分类_3.选股, "VIP用户"),
    ],
)
def test_check_create_quota_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    vip_user_headers,
    root_user_headers,
    category,
    装备分类,
    user_type,
    mocker,
):
    """获取用户组合指标配置列表"""
    if user_type == "超级用户":
        header = root_user_headers
    elif user_type == "VIP用户":
        header = vip_user_headers
    else:
        header = free_user_headers
    params = {"装备分类": 装备分类} if 装备分类 else {}
    if user_type == "免费用户":
        response = fixture_client.get(f"user/{category}/quota/check", params=params, headers=header)
        assert response.status_code == 400
        assert response.json()["message"] == "权限不存在"
    else:

        async def mock_创建数量限制(*args, **kwargs):
            ...

        async def mock_except(*args, **kwargs):
            raise CreateQuantityLimit()

        mocker.patch("app.api.api_v1.endpoints.user.创建数量限制", side_effect=mock_创建数量限制)
        response = fixture_client.get(f"user/{category}/quota/check", params=params, headers=header)
        assert response.status_code == 200
        assert response.json()["result"] == "success"
        # error
        mocker.patch("app.api.api_v1.endpoints.user.创建数量限制", side_effect=mock_except)
        response = fixture_client.get(f"user/{category}/quota/check", params=params, headers=header)
        assert response.status_code == 400
        assert response.json()["message"] == f"创建数达到上限"


def test_mfrs_create_view(
    fixture_client,
    fixture_settings,
    client_user_data,
    free_user_headers,
    root_user_headers,
    mocker,
):
    m_get_or_create_disc_user = mocker.patch("app.crud.user.get_or_create_disc_user", side_effect=mock_get_or_create_disc_user)
    m_update_user_signature = mocker.patch("app.crud.user.update_user_signature", side_effect=mock_update_user_signature)
    response = fixture_client.post(f"user/manufacturer", json=client_user_data, headers=free_user_headers)
    assert response.status_code == 400
    assert response.json()["message"] == "权限不足，请联系客服或者管理员"
    response = fixture_client.post(f"user/manufacturer", json=client_user_data, headers=root_user_headers)
    assert response.status_code == 201
    assert response.json()["client"]["indicator"] == fixture_settings.mfrs.CLIENT_INDICATOR
    assert m_get_or_create_disc_user.called
    assert m_update_user_signature.called


@mark.parametrize(
    "update_data",
    [
        ({"name": "client_name", "value": "test_001"}),
        ({"name": "client.base_url", "value": "http://base_url"}),
    ],
)
def test_mfrs_update_view(
    fixture_client,
    fixture_settings,
    logined_client_user,
    free_user_headers,
    root_user_headers,
    update_data,
):
    username = logined_client_user["user"]["username"]
    params = {"data": update_data}
    response = fixture_client.put(f"user/manufacturer/{username}", json=params, headers=free_user_headers)
    assert response.status_code == 400
    assert response.json()["message"] == "权限不足，请联系客服或者管理员"
    response = fixture_client.put(f"user/manufacturer/{username}", json=params, headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["client"]["indicator"] == fixture_settings.mfrs.CLIENT_INDICATOR


def test_manufacturer_user_delete_view(fixture_client, client_user_by_delete, root_user_headers, free_user_headers, mocker):
    #
    response = fixture_client.post(f"user/manufacturer", json=client_user_by_delete, headers=root_user_headers)
    assert response.status_code == 201
    username = client_user_by_delete["user"]["username"]
    # not super user
    response = fixture_client.delete(f"user/manufacturer/{username}", headers=free_user_headers)
    assert response.status_code == 400
    assert response.json()["message"] == "权限不足，请联系客服或者管理员"
    # exist strategy
    m_check_strategy_exist = mocker.patch("app.api.api_v1.endpoints.user.check_strategy_exist", side_effect=mock_check_strategy_exist_with_true)
    response = fixture_client.delete(f"user/manufacturer/{username}", headers=root_user_headers)
    assert response.status_code == 400
    assert response.json()["message"] == "存在已创建的装备或者机器人，不允许删除该用户"
    assert m_check_strategy_exist.called
    # ok
    m_check_strategy_exist = mocker.patch("app.api.api_v1.endpoints.user.check_strategy_exist", side_effect=mock_check_strategy_exist_with_false)
    response = fixture_client.delete(f"user/manufacturer/{username}", headers=root_user_headers)
    assert response.status_code == 200
    assert m_check_strategy_exist.called
