from datetime import date, timedelta, datetime

from bson import ObjectId
from stralib import FastTdate

from app.crud.base import get_portfolio_collection
from app.enums.portfolio import 风险点状态
from tests.mocks.signal import (
    mock_check_equip_status_failed,
    mock_empty_dataframe,
    mock_get_strategy_signal,
)


def test_screen_strategy_signal_list_view(
    fixture_client, fixture_settings, free_user_headers, fixture_portfolio, mocker
):
    """获取选股策略信号列表"""
    if datetime.today().hour < 17:
        current_date = FastTdate.last_tdate(date.today())
    else:
        current_date = date.today()
    # 查询当天选股策略信号
    mocker.patch("app.service.signal.get_strategy_signal", mock_get_strategy_signal)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/screens/{fixture_portfolio['_id']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["signal_date"] == current_date.strftime("%Y-%m-%d")
    # 查询历史选股策略信号
    search_date = FastTdate.last_tdate(current_date - timedelta(days=5))
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/screens/{fixture_portfolio['_id']}",
        params={"search_date": search_date},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["signal_date"] == search_date.strftime("%Y-%m-%d")
    # 查询未来选股策略信号
    search_date = FastTdate.next_tdate(current_date + timedelta(days=5))
    mocker.patch("app.service.signal.get_strategy_signal", mock_empty_dataframe)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/screens/{fixture_portfolio['_id']}",
        params={"search_date": search_date},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


def test_timing_signal_get_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_portfolio,
    fixture_portfolio_with_self_robot,
    mocker,
):
    """获取择时策略信号"""
    # mock signal为空
    mocker.patch(
        "app.api.api_v1.endpoints.signal.get_signal_date",
        lambda *args: date.today() + timedelta(days=5),
    )
    mocker.patch("app.service.signal.get_strategy_signal", mock_empty_dataframe)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/timing/{fixture_portfolio['_id']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() is None
    # 当日
    mocker.patch(
        "app.api.api_v1.endpoints.signal.get_signal_date",
        lambda *args: date(2020, 9, 8),
    )
    mocker.patch("app.service.signal.get_strategy_signal", mock_get_strategy_signal)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/timing/{fixture_portfolio['_id']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["trade_date"] == "2021-05-17"
    assert response.json()["market_trend"] == "下降"
    # 当天数据未准备完毕，显示昨天的信号
    mocker.patch(
        "app.service.signal.date",
        type("MockTime", (), {"today": lambda *args: date(2020, 9, 8)}),
    )  # mock date.today 返回date(2020,9,8)
    mocker.patch(
        "app.service.signal.CheckStatus.check_equip_status_by_sid",
        mock_check_equip_status_failed,
    )
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/timing/{fixture_portfolio['_id']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["trade_date"] == "2021-05-17"
    assert response.json()["market_trend"] == "下降"
    # 组合选择的机器人无择时装备
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/timing/{fixture_portfolio_with_self_robot['_id']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() is None


def test_timing_signal_list_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_portfolio,
    fixture_portfolio_with_self_robot,
    mocker,
):
    """获取择时策略信号列表"""
    mocker.patch("app.service.signal.get_strategy_signal", mock_get_strategy_signal)
    start_date, end_date = date(2020, 9, 1), date(2020, 9, 4)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/timings/{fixture_portfolio['_id']}",
        params={"start_date": start_date, "end_date": end_date},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    # signal为空
    mocker.patch("app.service.signal.get_strategy_signal", mock_empty_dataframe)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/timings/{fixture_portfolio['_id']}",
        params={"start_date": start_date, "end_date": end_date},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == []
    # 组合选择的机器人无择时装备
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/timings/{fixture_portfolio_with_self_robot['_id']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


def test_risk_signal_list_view(
    fixture_client,
    fixture_settings,
    fixture_db,
    event_loop,
    free_user_headers,
    fixture_portfolio_sci_risk,
):
    """个股风险信号列表"""
    portfolio_id = fixture_portfolio_sci_risk["_id"]
    risks = []
    for risk in fixture_portfolio_sci_risk["risks"]:
        risk["status"] = 风险点状态.unresolved
        risks.append(risk)
    event_loop.run_until_complete(
        get_portfolio_collection(fixture_db).update_one(
            {"_id": ObjectId(portfolio_id)}, {"$set": {"risks": risks}}
        )
    )
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/risks/{portfolio_id}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_trade_strategy_signal_list_view(
    fixture_client, fixture_settings, free_user_headers, fixture_portfolio, mocker
):
    mocker.patch("app.service.signal.get_strategy_signal", mock_get_strategy_signal)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/signal/trades/{fixture_portfolio['_id']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
