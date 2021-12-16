import asyncio

from app.core.errors import LoginError
from app.global_var import G
from tests.mocks.message import MockSendSMS, MockSendMessage


def test_send_sms_view(fixture_client, fixture_settings, logined_free_user, mocker):
    mobile = logined_free_user["user"]["mobile"]
    mocker.patch("app.api.api_v1.endpoints.authentication.SendMessage", side_effect=MockSendMessage)
    mocker.patch("app.api.api_v1.endpoints.authentication.SendSMS", side_effect=MockSendSMS)
    response = fixture_client.post(f"{fixture_settings.url_prefix}/auth/code", json={"mobile": mobile})
    assert response.status_code == 200
    assert "sms_code" in response.json().keys()
    assert response.json()["sms_code"] == fixture_settings.sms.fixed_code


def test_verify_code_view(fixture_client, fixture_settings, logined_free_user, mocker):
    mobile = logined_free_user["user"]["mobile"]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/auth/verify_code", json={"mobile": mobile, "code": fixture_settings.sms.fixed_code})
    assert response.status_code == 200
    assert response.json()["result"] == "success"


def test_login_with_sms_view(fixture_client, fixture_settings, logined_free_user, mocker):
    mobile = logined_free_user["user"]["mobile"]
    # 关闭短信认证
    fixture_settings.sms.switch = False
    data = {"user": {"mobile": mobile, "code": fixture_settings.sms.fixed_code}}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/auth/sms_login", json=data)
    assert response.status_code == 200
    assert "token" in response.json().keys()
    # 短信认证
    fixture_settings.sms.switch = True

    async def mock_verify_code_with_true(*args, **kwargs):
        return True

    async def mock_verify_code_with_false(*args, **kwargs):
        raise LoginError(message="验证码过期失效")

    m_verify_code = mocker.patch("app.api.api_v1.endpoints.authentication.verify_code", side_effect=mock_verify_code_with_true)
    data = {"user": {"mobile": mobile, "code": "111111"}}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/auth/sms_login", json=data)
    assert response.status_code == 200
    assert "token" in response.json().keys()
    assert m_verify_code.called
    m_verify_code = mocker.patch("app.api.api_v1.endpoints.authentication.verify_code", side_effect=mock_verify_code_with_false)
    response = fixture_client.post(f"{fixture_settings.url_prefix}/auth/sms_login", json=data)
    assert response.status_code == 400
    assert response.json()["message"] == "验证码过期失效"
    assert m_verify_code.called
    fixture_settings.sms.switch = False  # 恢复配置
