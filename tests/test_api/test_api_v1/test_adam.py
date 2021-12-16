import base64
import pickle

from tests.mocks.signal import mock_get_strategy_flow, mock_get_strategy_signal


def test_get_adam_signal(fixture_client, fixture_settings, free_user_headers, mocker):
    """查询策略信号"""
    # ====robot
    # wrong
    params = {"sid": "10000000000000", "start_datetime": "2020-07-24 00:00:00", "end_datetime": "2020-07-14 00:00:00"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/adam/signal/", params=params, headers=free_user_headers)
    assert response.status_code == 400
    assert response.text == '{"errors":{"body":["查询装备列表发生错误，错误信息: start date (2020-07-24 00:00:00) cannot be greater than end date (2020-07-14 00:00:00)!"]}}'
    # right
    params = {"sid": "10000000000000", "start_datetime": "2020-07-14 00:00:00", "end_datetime": "2020-07-14 00:00:00"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/adam/signal/", params=params, headers=free_user_headers)
    assert response.status_code == 200
    df = pickle.loads(base64.b64decode(response.text))
    assert df.empty is True
    # ====equipment
    # wrong
    params = {"sid": "10000000000000", "start_datetime": "2020-07-24 00:00:00", "end_datetime": "2020-07-14 00:00:00"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/adam/signal/", params=params, headers=free_user_headers)
    assert response.status_code == 400
    assert response.text == '{"errors":{"body":["查询装备列表发生错误，错误信息: start date (2020-07-24 00:00:00) cannot be greater than end date (2020-07-14 00:00:00)!"]}}'
    # right
    params = {"sid": "10000000000000", "start_datetime": "2020-07-14 00:00:00", "end_datetime": "2020-07-14 00:00:00"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/adam/signal/", params=params, headers=free_user_headers)
    assert response.status_code == 200
    df = pickle.loads(base64.b64decode(response.text))
    assert df.empty is True
    mocker.patch("app.api.api_v1.endpoints.adam.get_strategy_signal", mock_get_strategy_signal)
    params = {"sid": "02000000000000_0", "start_datetime": "2020-07-14 00:00:00", "end_datetime": "2020-07-14 00:00:00"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/adam/signal/", params=params,
                                  headers=free_user_headers)
    assert response.status_code == 200
    df = pickle.loads(base64.b64decode(response.text))
    assert df.empty is False


def test_get_adam_flow(fixture_client, fixture_settings, free_user_headers, mocker):
    """查询机器人流水数据"""
    # wrong
    params = {"sid": "02000000000000_0", "start_datetime": "2020-07-14 00:00:00", "end_datetime": "2020-07-14 00:00:00"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/adam/flow/", params=params, headers=free_user_headers)
    assert response.status_code == 400
    assert '"查询机器人列表发生错误，错误信息: 02000000000000_0 table Not Exits' in response.text
    # right
    mocker.patch("app.api.api_v1.endpoints.adam.get_strategy_flow", mock_get_strategy_flow)
    params = {"sid": "10000000000000", "start_datetime": "2020-07-14 00:00:00", "end_datetime": "2020-07-14 00:00:00"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/adam/flow/", params=params, headers=free_user_headers)
    assert response.status_code == 200
    df = pickle.loads(base64.b64decode(response.text))
    assert df.empty is False
