from datetime import datetime

import pytest
from pandas import DataFrame, Index, Timestamp

from app.models.base.stock import 自选股股票
from app.schema.stock import FavoriteStockInResponse
from app.service.datetime import get_early_morning
from app.service.message.send import (
    get_all_equipment_signals,
    get_appointed_real_signal,
    get_equipment_signal,
    get_equipment_signal_by_user,
    get_package_signal,
    send_message,
)
from tests.consts.signal import const_signal
from tests.mocks.signal import (
    mock_get_equipment_signal,
    mock_get_strategy_signal,
    mock_获取大类资产配置信号列表,
    mock_获取择时信号列表,
    mock_获取选股信号列表,
)

pytestmark = pytest.mark.asyncio


async def test_get_package_signal(
    fixture_client, fixture_db, logined_free_user, fixture_create_equipments, mocker
):
    tdate = get_early_morning()

    async def mock_get_favorite_stock_by_unique(*args):
        stocks = [
            自选股股票(symbol=s, exchange="1" if e == "CNSESH" else "0")
            for s, e in zip(
                const_signal["风控包"][0]["data"]["symbol"],
                const_signal["风控包"][0]["data"]["exchange"],
            )
        ]
        return FavoriteStockInResponse(username="", stocks=stocks)

    fake_get_strategy_signal = mocker.patch(
        "app.service.message.send.get_strategy_signal",
        side_effect=mock_get_strategy_signal,
    )
    fake_get_favorite_stock_by_unique = mocker.patch(
        "app.service.message.send.get_favorite_stock_by_unique",
        side_effect=mock_get_favorite_stock_by_unique,
    )
    equipment = [x for x in fixture_create_equipments if x["名称"] == "test风控一号"][0]
    response = await get_package_signal(
        fixture_db, equipment["标识符"], tdate, tdate, logined_free_user["user"]
    )
    assert isinstance(response, DataFrame)
    assert fake_get_strategy_signal.called
    assert fake_get_favorite_stock_by_unique.called
    assert response.empty is False


async def test_get_appointed_real_signal(
    fixture_client,
    fixture_db,
    fixture_create_equipments,
    fixture_insert_equipment_backtest_real_data,
):
    tdate = datetime.strptime("2019-01-01", "%Y-%m-%d")
    equipment = [x for x in fixture_create_equipments if x["名称"] == "test大类资产配置"][0]
    response = await get_appointed_real_signal(
        fixture_db, equipment["标识符"], tdate, tdate
    )
    assert isinstance(response, DataFrame)
    assert "时间" in response.columns.tolist()
    assert "股票代码" in response.columns.tolist()


@pytest.mark.skip
async def test_get_equipment_signal(
    fixture_client, fixture_db, fixture_create_equipments, mocker
):
    tdate = get_early_morning()
    # 获取选股信号列表
    mocker.patch("app.service.message.send.获取选股信号列表", mock_获取选股信号列表)
    response = await get_equipment_signal(
        fixture_db, fixture_create_equipments[0], tdate, tdate
    )
    assert isinstance(response, DataFrame)
    assert "日期" in response.columns.tolist()
    assert "股票代码" in response.columns.tolist()
    # 获取择时信号列表
    mocker.patch("app.service.message.send.获取择时信号列表", mock_获取择时信号列表)
    response = await get_equipment_signal(
        fixture_db, fixture_create_equipments[6], tdate, tdate
    )
    assert isinstance(response, DataFrame)
    assert "信号日期" in response.columns.tolist()
    assert "指数" in response.columns.tolist()
    # 大类资产配置、基金定投装备信号
    mocker.patch(
        "app.service.message.send.get_appointed_real_signal", mock_获取大类资产配置信号列表
    )
    response = await get_equipment_signal(
        fixture_db, fixture_create_equipments[14], tdate, tdate
    )
    assert isinstance(response, DataFrame)
    assert "时间" in response.columns.tolist()
    assert "股票代码" in response.columns.tolist()


async def test_get_all_equipment_signals(
    fixture_client, fixture_db, fixture_create_equipments, mocker
):
    mocker.patch(
        "app.service.message.send.get_equipment_signal", mock_get_equipment_signal
    )
    tdate = get_early_morning(datetime.strptime("2020-11-05", "%Y-%m-%d"))
    filters = {"标识符": fixture_create_equipments[0]["标识符"]}
    response = await get_all_equipment_signals(fixture_db, tdate, filters)
    assert isinstance(response, dict)
    assert fixture_create_equipments[0]["标识符"] in response.keys()


async def test_get_equipment_signal_by_user(
    fixture_client,
    fixture_settings,
    fixture_db,
    logined_free_user,
    fixture_create_equipments,
):
    await fixture_db[fixture_settings.db.DB_NAME][
        fixture_settings.collections.USER
    ].update_one(
        {"username": logined_free_user["user"]["username"]},
        {
            "$set": {
                "equipment": {
                    "subscribe_info": {
                        "fans_num": 0,
                        "focus_num": 0,
                        "focus_list": ["02000000test01"],
                    },
                    "create_info": {
                        "create_num": 0,
                        "running_list": [
                            "02000000test01",
                            "03000000test02",
                            "06000000test10",
                        ],
                        "closed_list": [],
                    },
                    "msg_num": 0,
                }
            }
        },
    )
    user = await fixture_db[fixture_settings.db.DB_NAME][
        fixture_settings.collections.USER
    ].find_one({"username": logined_free_user["user"]["username"]})
    tdate = get_early_morning()
    signals = {
        fixture_create_equipments[0]["标识符"]: {
            "signal": await mock_获取选股信号列表(),
            "equipment": fixture_create_equipments[0],
        },
        fixture_create_equipments[6]["标识符"]: {
            "signal": await mock_获取择时信号列表(),
            "equipment": fixture_create_equipments[6],
        },
        fixture_create_equipments[14]["标识符"]: {
            "signal": await mock_获取大类资产配置信号列表(),
            "equipment": fixture_create_equipments[14],
        },
    }
    response = await get_equipment_signal_by_user(fixture_db, user, tdate, signals)
    assert isinstance(response, str)
    assert fixture_create_equipments[0]["名称"] in response
