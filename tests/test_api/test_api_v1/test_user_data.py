from tests.mocks.signal import mock_get_strategy_signal


def test_user_data_message(fixture_client, fixture_settings, vip_user_headers, mocker):
    """用户订阅装备发送邮件消息"""
    fake_get_strategy_signal = mocker.patch("app.service.strawman_data.get_strategy_signal", side_effect=mock_get_strategy_signal)
    # 装备
    response = fixture_client.get(f"{fixture_settings.url_prefix}/user_data/message", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["result"] == "success"
    assert fake_get_strategy_signal.called
