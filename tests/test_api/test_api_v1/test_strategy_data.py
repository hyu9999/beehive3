import csv
import json
import os
from datetime import datetime

import pytest
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pytest import mark
from stralib import get_strategy_signal

from app.crud.strategy_data import 查询最新策略数据
from app.enums.strategy import 策略分类
from app.enums.strategy_data import 策略名称, 策略数据类型
from app.service.strategy_data import get_strategy_model_by_name, delete_adam_strategy_signal
from tests.fixtures.strategy import fake_strategy_info
from tests.fixtures.strategy_data import test_strategy_data
from tests.mocks.db_base import MockConfigCollection
from tests.mocks.equipment import mock_nothing
from tests.mocks.strategy_data import mock_创建策略数据, mock_删除策略数据, mock_查询策略数据


def test_create_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    root_user_headers,
    mocker,
):
    mocker.patch("app.crud.strategy_data.创建策略数据", mock_创建策略数据)
    mocker.patch("app.crud.strategy_data.策略数据完整性检验", mock_nothing)
    # 权限不足
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/strategy_data/{策略名称.择时装备}/{策略数据类型.回测指标}",
        json=jsonable_encoder([test_strategy_data["择时"]["回测指标"]]),
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 传入列表不能为空
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/strategy_data/{策略名称.择时装备}/{策略数据类型.回测指标}",
        json=[],
        headers=root_user_headers,
    )
    assert response.status_code == 400
    assert "传入列表不能为空" in response.text
    # 正向
    params = {}
    for s_name in 策略名称:
        for s_type in 策略数据类型:
            response = fixture_client.post(
                f"{fixture_settings.url_prefix}/strategy_data/{s_name}/{s_type}",
                json=jsonable_encoder(
                    [test_strategy_data[s_name][s_type]] if isinstance(test_strategy_data[s_name][s_type], dict) else test_strategy_data[s_name][s_type]
                ),
                params=params,
                headers=root_user_headers,
            )
            assert response.status_code == 200
            assert response.json() == {"result": "success"}


def test_get_view(fixture_client, fixture_settings, free_user_headers, root_user_headers, mocker):
    mocker.patch("app.crud.strategy_data.查询策略数据", mock_查询策略数据)
    mocker.patch("app.crud.strategy_data.策略数据完整性检验", mock_nothing)
    # 权限不足
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/strategy_data/{策略名称.选股装备}/{策略数据类型.回测评级}/{test_strategy_data[策略名称.选股装备][策略数据类型.回测评级][0]['标识符']}",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 排序
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/strategy_data/{策略名称.选股装备}/{策略数据类型.回测评级}/{test_strategy_data[策略名称.选股装备][策略数据类型.回测评级][0]['标识符']}?排序=数据集&排序方式=倒序",
        headers=root_user_headers,
    )
    assert response.status_code == 200
    # 正向
    for s_name in 策略名称:
        for s_type in 策略数据类型:
            s_dict = test_strategy_data[s_name][s_type] if isinstance(test_strategy_data[s_name][s_type], dict) else test_strategy_data[s_name][s_type][0]
            params = {}
            if s_type == 策略数据类型.回测评级:
                if s_name == 策略名称.择时装备:
                    params["回测年份"] = s_dict["回测年份"]
                else:
                    params["数据集"] = "整体评级"
            else:
                params["start"] = params["end"] = s_dict["交易日期"].strftime("%Y-%m-%d") if "交易日期" in s_dict.keys() else None
            response = fixture_client.get(
                f"{fixture_settings.url_prefix}/strategy_data/{s_name}/{s_type}/{s_dict['标识符']}",
                params=params,
                headers=root_user_headers,
            )
            assert response.status_code == 200


def test_delete_view(fixture_client, fixture_settings, free_user_headers, root_user_headers, mocker):
    mocker.patch("app.crud.strategy_data.删除策略数据", mock_删除策略数据)

    # 权限不足
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/strategy_data/{策略名称.机器人}/{策略数据类型.回测评级}/{test_strategy_data[策略名称.机器人][策略数据类型.回测评级][0]['标识符']}",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正向
    for s_name in 策略名称:
        for s_type in 策略数据类型:
            sid = (
                test_strategy_data[s_name][s_type][0]["标识符"]
                if isinstance(test_strategy_data[s_name][s_type], list)
                else test_strategy_data[s_name][s_type]["标识符"]
            )
            fixture_client.delete(
                f"{fixture_settings.url_prefix}/strategy_data/{s_name}/{s_type}/{sid}",
                headers=root_user_headers,
            )


@mark.parametrize(
    "strategy_name,strategy_type,sid",
    [
        (策略名称.机器人, 策略数据类型.回测信号, "10000000test01"),
        (策略名称.机器人, 策略数据类型.实盘指标, "10000000test01"),
        (策略名称.选股装备, 策略数据类型.回测信号, "02000000test01"),
        (策略名称.选股装备, 策略数据类型.实盘指标, "02000000test01"),
    ],
)
def test_latest_view(fixture_client, root_user_headers, strategy_name, strategy_type, sid, mocker):
    async def mock_查询最新策略数据(*args):
        if strategy_type not in [strategy_type.实盘信号, strategy_type.实盘指标]:
            raise HTTPException(422, detail="错误的策略数据类型")
        class_model = get_strategy_model_by_name(strategy_name, strategy_type)
        return class_model(**test_strategy_data[strategy_name][strategy_type])

    m_func = mocker.patch("app.api.api_v1.endpoints.strategy_data.查询最新策略数据", side_effect=mock_查询最新策略数据)
    response = fixture_client.get(
        f"strategy_data/{strategy_name}/{strategy_type}/{sid}/latest",
        headers=root_user_headers,
    )
    if strategy_type in [策略数据类型.实盘指标, 策略数据类型.实盘信号]:
        assert response.status_code == 200
    else:
        assert response.status_code == 422
    assert m_func.called


@mark.asyncio
@mark.parametrize(
    "strategy_name,strategy_type,sid",
    [
        (策略名称.机器人, 策略数据类型.回测信号, fake_strategy_info[策略分类.机器人]["已上线"]["标识符"]),
        (策略名称.选股装备, 策略数据类型.回测信号, fake_strategy_info[策略分类.选股]["已上线"]["标识符"]),
        (策略名称.机器人, 策略数据类型.实盘指标, fake_strategy_info[策略分类.机器人]["已上线"]["标识符"]),
        (策略名称.选股装备, 策略数据类型.实盘指标, fake_strategy_info[策略分类.选股]["已上线"]["标识符"]),
        (策略名称.选股装备, 策略数据类型.实盘指标, fake_strategy_info[策略分类.选股]["已下线"]["标识符"]),
    ],
)
async def test_查询最新策略数据(fixture_db, strategy_name, strategy_type, sid, mocker):
    m_func = mocker.patch("app.crud.strategy_data.get_collection_by_config", side_effect=MockConfigCollection)
    if strategy_type in [策略数据类型.实盘指标, 策略数据类型.实盘信号]:
        response = await 查询最新策略数据(fixture_db, strategy_name, strategy_type, sid)
        assert isinstance(response, get_strategy_model_by_name(strategy_name, strategy_type))
        assert m_func.called
    else:
        with pytest.raises(HTTPException) as exc_info:
            await 查询最新策略数据(fixture_db, strategy_name, strategy_type, sid)
            assert exc_info.value == "错误的策略数据类型"


def test_create_by_id_view(
    fixture_client, fixture_db, client_user_headers, fixture_create_screen_equipment, fixture_screen_equipment_with_manual_transfer, mocker
):
    none_sid = "02000000000009"
    sid = fixture_screen_equipment_with_manual_transfer["标识符"]
    dt = datetime.strptime("20210603", "%Y%m%d")
    signal_list = [{"TDATE": dt.strftime("%Y-%m-%d %H:%M:%S"), "EXCHANGE": "CNSESZ", "SYMBOL": "000002", "TCLOSE": 2.2696, "SCORE": 1}]
    params = {"data": json.dumps(signal_list)}

    class Mock_AirflowTools:
        def wait_dag_run(self, dag_id):
            ...

    mocker.patch("app.api.api_v1.endpoints.strategy_data.AirflowTools", side_effect=Mock_AirflowTools)
    # equipment not exist
    response = fixture_client.post(f"strategy_data/选股/adam/{none_sid}", headers=client_user_headers, json=params)
    assert response.status_code == 400
    assert response.json()["message"] == "装备不存在"
    # 信号传入方式错误
    response = fixture_client.post(f"strategy_data/选股/adam/{fixture_create_screen_equipment['标识符']}", headers=client_user_headers, json=[])
    assert response.status_code == 400
    assert response.json()["message"] == "传入参数错误，错误原因：信号传入方式错误不允许写入策略数据"
    # no data
    response = fixture_client.post(f"strategy_data/选股/adam/{sid}", headers=client_user_headers, json=[])
    assert response.status_code == 400
    assert response.json()["message"] == "创建策略数据失败，错误原因：传入列表不能为空"
    # 单传数据
    response = fixture_client.post(f"strategy_data/选股/adam/{sid}", headers=client_user_headers, data=params)
    assert response.status_code == 200
    signals = get_strategy_signal(sid, dt.strftime("%Y%m%d"), dt.strftime("%Y%m%d"))
    assert len(signals) == 1
    delete_adam_strategy_signal(sid)
    # 生成文件
    file_name = "20210603-108.csv"
    with open(file_name, "a+") as f:
        csv_writer = csv.writer(f)
        # header
        csv_writer.writerow(["", "stkcode", "stkname", "diff", "date", "exchange", "stock", "preclose"])
        # content
        csv_writer.writerow(["0", "601919", "中远海控", "2022", "20210603", "CNSESH", "CNSESH601919", 21.24])
        csv_writer.writerow(["1", "688136", "科兴制药", "1811", "20210603", "CNSESH", "CNSESH688136", 47.51])
    # 单传文件
    files = [("file", (file_name, open(file_name, "rb"), "text/csv"))]
    response = fixture_client.post(f"strategy_data/选股/adam/{sid}", headers=client_user_headers, files=files)
    assert response.status_code == 200
    signals = get_strategy_signal(sid, dt.strftime("%Y%m%d"), dt.strftime("%Y%m%d"))
    assert len(signals) == 2
    delete_adam_strategy_signal(sid)
    # 数据和文件
    files = [("file", (file_name, open(file_name, "rb"), "text/csv"))]
    response = fixture_client.post(f"strategy_data/选股/adam/{sid}", headers=client_user_headers, data=params, files=files)
    assert response.status_code == 200
    signals = get_strategy_signal(sid, dt.strftime("%Y%m%d"), dt.strftime("%Y%m%d"))
    assert len(signals) == 3
    delete_adam_strategy_signal(sid)
    os.remove(file_name)
