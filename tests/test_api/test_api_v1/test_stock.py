import copy

from datetime import datetime
import pytest
from pytest import mark

from app.enums.security import 证券交易所
from app.schema.stock import 股票InResponse

pytestmark = pytest.mark.asyncio


@pytest.fixture
def favorite_stock_data(logined_free_user):
    data = {
        "username": logined_free_user["user"]["username"],
        "stocks": [
            {"symbol": "000001", "exchange": "0", "share_cost_price": None, "stop_profit": 9999.0, "stop_loss": 0.0},
            {"symbol": "000002", "exchange": "0", "share_cost_price": None, "stop_profit": 9999.0, "stop_loss": 0.0},
        ],
        "category": "portfolio",
    }
    return data


def _delete_favorite_stock(fixture_settings, fixture_db):
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.FAVORITE_STOCK].delete_many({"username": {"$regex": "^test"}})


@pytest.fixture
def fixture_favorite_stock(fixture_client, fixture_settings, fixture_db, free_user_headers, favorite_stock_data):
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert response.status_code == 200
    assert len(response.json()["stocks"]) == 2
    assert response.json()["stocks"][0]["symbol"] == "000001"
    yield response.json()
    _delete_favorite_stock(fixture_settings, fixture_db)


def test_get_favorite_stocks_list_view(fixture_client, fixture_settings, fixture_db, free_user_headers, fixture_favorite_stock):
    response = fixture_client.get(f"{fixture_settings.url_prefix}/stock/favorite/?category=portfolio", headers=free_user_headers)
    assert response.status_code == 200
    assert len(response.json()[0]["stocks"]) == 2


def test_create_favorite_stock_view_with_same_stock(fixture_client, fixture_settings, fixture_db, free_user_headers, favorite_stock_data):
    """测试当json数据中有俩个相同的股票时，是否能正确添加自选股股票"""
    stock = favorite_stock_data["stocks"][0]
    stock["stop_profit"] = 8888.0
    favorite_stock_data["stocks"].append(stock)
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert response.status_code == 200
    assert len(response.json()["stocks"]) == 3
    assert response.json()["stocks"][0]["stop_profit"] == 8888.0
    _delete_favorite_stock(fixture_settings, fixture_db)


def test_create_favorite_stock_view(
        fixture_client, fixture_settings, fixture_db, free_user_headers, favorite_stock_data):
    """测试在添加新自选股后老的自选股还在."""
    old_stock = favorite_stock_data["stocks"][0]
    new_stock = favorite_stock_data["stocks"][-1]
    favorite_stock_data["stocks"] = [old_stock]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert response.status_code == 200
    favorite_stock_data["stocks"] = [new_stock]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert len(response.json()["stocks"]) == 2


def test_create_favorite_stock_view_with_new_stock(
    fixture_client, fixture_settings, fixture_db, free_user_headers, fixture_favorite_stock, favorite_stock_data
):
    """测试当同一用户同一类型已存在自选股对象时，能否正确添加自选股股票"""
    stock1, stock2 = copy.deepcopy(favorite_stock_data["stocks"][:2])
    stock1["symbol"] = "000003"
    stock2["stop_profit"] = 6666.0
    favorite_stock_data["stocks"].extend([stock1, stock2])
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert response.status_code == 200
    assert len(response.json()["stocks"]) == 4
    assert response.json()["stocks"][0]["stop_profit"] == 9999.0
    _delete_favorite_stock(fixture_settings, fixture_db)


def test_create_favorite_stock_view_with_diff_category(
    fixture_client, fixture_settings, free_user_headers, fixture_favorite_stock, favorite_stock_data, equipments_data_in_db
):
    """测试当同一用户同一类型已存在自选股对象时，能否正确新增不同类型的自选股对象"""
    favorite_stock_data["category"] = "equipment"
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert response.status_code == 422
    assert "入参错误，请传入正确的标识符" in response.text
    favorite_stock_data["sid"] = equipments_data_in_db[0]["标识符"]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["category"] == "equipment"
    assert response.json()["_id"] != fixture_favorite_stock["_id"]


@mark.skip
def test_get_stock_k_line_view(fixture_client, fixture_settings):
    data = {"symbol": "600519", "exchange": 证券交易所.上证}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/stock/five_real_time_price", params=data)
    assert response.status_code == 200
    assert "bjw1" in response.json().keys()
    data["exchange"] = 证券交易所.深证
    response = fixture_client.get(f"{fixture_settings.url_prefix}/stock/five_real_time_price", params=data)
    assert response.status_code == 400
    assert "获取五档图失败，错误信息: 未找到股票600519.SZ的ticks数据." in response.text


def test_delete_favorite_stock_view(fixture_client, fixture_settings, free_user_headers, fixture_favorite_stock, favorite_stock_data):
    """删除自选股"""
    stock = favorite_stock_data["stocks"][0]
    symbol, category = stock["symbol"], favorite_stock_data["category"]
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/stock/favorite/", params={"symbol": symbol, "category": category}, headers=free_user_headers
    )
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/stock/favorite/", params={"username": favorite_stock_data["username"], "category": category}, headers=free_user_headers
    )
    assert response.status_code == 200
    assert symbol not in [stock["symbol"] for stock in response.json()[0]["stocks"]]
    # 测试非组合类型自选股删除
    favorite_stock_data["category"] = "equipment"
    favorite_stock_data["sid"] = "test_equipment"
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/favorite/", json=favorite_stock_data, headers=free_user_headers)
    assert response.status_code == 200
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/stock/favorite/", params={"symbol": symbol, "category": "equipment"}, headers=free_user_headers
    )
    assert response.status_code == 400
    assert "缺少必填参数sid" in response.text
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/stock/favorite/", params={"symbol": symbol, "category": "equipment", "sid": "test_equipment"}, headers=free_user_headers
    )
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1


def test_get_swl2_industry_list_view(fixture_client, fixture_settings, free_user_headers):
    response = fixture_client.get(f"{fixture_settings.url_prefix}/stock/swl2_industry_list/", headers=free_user_headers)
    assert response.status_code == 200


@mark.skip
def test_market_index_data_view(fixture_client, fixture_settings, free_user_headers, mocker):
    def candlestickchart_mocker(*args, **kwargs):
        class CandlestickChartMocker:
            def __init__(self, *args, **kwargs):
                ...

            def market(*args, **kwargs):
                return [{"开盘价": 688}]

        return CandlestickChartMocker

    mocker.patch("app.api.api_v1.endpoints.stock.CandlestickChart", side_effect=candlestickchart_mocker())
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/stock/market_index_data?symbol=000001&start_date={datetime.today()}&" f"end_date={datetime.today()}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["开盘价"] == 688


def test_query_stock_list(fixture_client, fixture_settings, free_user_headers, mocker):
    stock_data = {"symbol": "test", "exchange": "0", "symbol_name": "test", "symbol_shortname": "test", "industry": "test"}

    async def coro(*args, **kwargs):
        return [股票InResponse(**stock_data)]

    mocker.patch("app.api.api_v1.endpoints.stock.查询股票列表", side_effect=coro)
    response = fixture_client.get(f"{fixture_settings.url_prefix}/stock/list", headers=free_user_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["industry"] == "test"


@mark.skip
def test_query_stock_hq(fixture_client, fixture_settings, free_user_headers, mocker):
    payload = {"stocks": [{"symbol": "test", "exchange": "0", "symbol_name": "test"}]}

    def mock_query_stock_price_from_jiantou(*args, **kwargs):
        return [
            {
                "symbol": "test",
                "symbol_name": "test",
                "exchange": "0",
                "previous_close_price": 0,
                "opening_price": 0,
                "today_low": 0,
                "today_high": 0,
                "realtime_price": 0,
            }
        ]

    mocker.patch("app.api.api_v1.endpoints.stock.query_stock_price_from_jiantou", side_effect=mock_query_stock_price_from_jiantou)
    response = fixture_client.post(f"{fixture_settings.url_prefix}/stock/hq", json=payload, headers=free_user_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["symbol"] == "test"
