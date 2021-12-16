import asyncio
import random
from datetime import datetime, timedelta

from fastapi.encoders import jsonable_encoder
from stralib import FastTdate

from app.crud.base import get_robots_collection, get_collection_by_config
from app.db.mongodb import get_database
from app.service.datetime import get_early_morning
from tests.consts.robots import (
    robot_backtest_indicator_data,
    robot_backtest_signal_data,
    robot_backtest_assess_data,
    robot_real_indicator_data,
    robot_real_signal_data,
)
from tests.mocks.robot import mock_get_client_robot_list, mock_empty_client_robot_list
from tests.mocks.signal import mock_update_stralib_robot_data
from tests.mocks.strategy_data import mock_get_strategy_data_list, mock_empty_strategy_data_list
from tests.mocks.topic import MockDisc, mock_create_thread


def test_get_a_robot_information(fixture_client, fixture_settings, vip_user_headers, root_user_headers, fixture_online_robot):
    """获取某机器人信息"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["标识符"] == fixture_online_robot["标识符"]
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}?show_detail=true", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["择时装备列表"][0]["标识符"] == fixture_online_robot["择时装备列表"][0]

    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/10000000000000", headers=vip_user_headers)
    assert response.status_code == 400
    assert "机器人不存在" in response.text


def test_query_robot_list(fixture_client, fixture_settings, vip_user_headers, root_user_data, root_user_headers, fixture_online_robot):
    """根据查询的条件返回满足条件的机器人列表信息"""
    test_sid = fixture_online_robot["标识符"]
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?标识符={test_sid}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == test_sid
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?标识符={test_sid}&标签=别的", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json() == []
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?标识符={test_sid}&名称={fixture_online_robot['名称']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == test_sid
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?名称={fixture_online_robot['名称']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == test_sid
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?作者={root_user_data['user']['username']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert test_sid in [i["标识符"] for i in response.json()]
    assert len(response.json()) == 1
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?上线时间=2019-01-02 00:00:00&标识符={test_sid}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json() == []
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?下线时间={get_early_morning()}&标识符={test_sid}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json() == []
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?状态=停止运行", headers=vip_user_headers)
    assert response.status_code == 422
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots?状态=审核中&作者={root_user_data['user']['username']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots?作者={root_user_data['user']['username']}&search_name=test&模糊查询=名称&is_paging=true", headers=vip_user_headers
    )
    assert response.status_code == 200
    assert response.json()["数据"][0]["标识符"] == test_sid
    assert response.json()["数据"][0]["名称"] == fixture_online_robot["名称"]


def test_query_my_robot_list(fixture_client, fixture_settings, free_user_headers):
    """查询我的机器人信息列表"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/my/list?排序=创建时间22", headers=free_user_headers)
    assert response.status_code == 422
    assert response.json() == {"errors": {"body": ["错误的排序类型"]}}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/my/list?筛选=我创建的机器人&排序=创建时间&排序方式=倒序", headers=free_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert [row["创建时间"] for row in data] == sorted([row["创建时间"] for row in data], reverse=True)  # 判断是否降序
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/my/list?排序=创建时间&排序方式=倒序", headers=free_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert [row["创建时间"] for row in data] == sorted([row["创建时间"] for row in data], reverse=True)


def test_create_new_robot(fixture_client, fixture_settings, vip_user_headers, fixture_robot_data_in_db, mocker):
    """新建机器人"""
    # 创建数量限制
    mocker.patch("app.service.robots.robot.settings.num_limit", {"VIP用户": {"robot": 6}})
    mocker.patch("app.settings.discuzq", MockDisc())
    mocker.patch("app.crud.robot.create_thread", mock_create_thread)
    create_data = {"机器人": jsonable_encoder(fixture_robot_data_in_db)}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/new?实时审核=false", json=create_data, headers=vip_user_headers)
    assert response.status_code == 200
    assert "标识符" in response.json()
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{response.json()['标识符']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["名称"] == fixture_robot_data_in_db["名称"]
    # 机器人已存在
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/new?实时审核=false", json=create_data, headers=vip_user_headers)
    assert response.status_code == 400
    assert "机器人已存在" in response.text


def test_test_create_tmp_robot(fixture_client, fixture_settings, vip_user_headers, root_user_headers, fixture_robot_data_in_db, mocker):
    """创建临时机器人"""
    mocker.patch("app.settings.discuzq", MockDisc())
    mocker.patch("app.crud.robot.create_thread", mock_create_thread)
    create_data = {"机器人": jsonable_encoder(fixture_robot_data_in_db)}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/backtest/robots/new", json=create_data, headers=vip_user_headers)
    assert response.status_code == 200
    assert "标识符" in response.json()
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{response.json()['标识符']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["名称"] == create_data["机器人"]["名称"]
    assert response.json()["状态"] == "临时回测"
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/robots/{response.json()['标识符']}", headers=root_user_headers)
    assert response.status_code == 200


def test_remove_robot(fixture_client, fixture_settings, free_user_headers, root_user_headers, fixture_online_robot):
    """删除某机器人"""
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}", headers=free_user_headers)
    assert response.status_code == 400
    assert "权限不足" in response.text
    # 删除1条
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json() == 1
    # 删除0条
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json() == 0


def test_get_robot_logo(fixture_client, fixture_settings, free_user_headers, fixture_online_robot, fixture_offline_robot):
    """获取机器人头像"""
    # robot_id 存在
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/logo/{fixture_online_robot['标识符']}", headers=free_user_headers)
    assert response.status_code == 200
    assert response.text == "i am a pic"

    # robot_id 不存在
    from string import ascii_lowercase
    from string import digits

    VALID_KEY_CHARS = f"{digits}{ascii_lowercase}"
    random_robot_id = "10" + "".join(random.sample(VALID_KEY_CHARS, 12))
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/logo/{random_robot_id}", headers=free_user_headers)
    assert response.status_code == 400
    assert "机器人不存在" in response.text
    # 文件不存在
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/logo/{fixture_offline_robot['标识符']}", headers=free_user_headers)
    assert response.status_code == 400
    assert "文件不存在" in response.text


def test_update_a_robot(fixture_client, fixture_settings, vip_user_headers, fixture_offline_robot):
    """更新机器人"""
    fixture_offline_robot["名称"] = "修改啦修改啦哈哈哈"
    fixture_offline_robot["上线时间"] = str(fixture_offline_robot["上线时间"])
    fixture_offline_robot["创建时间"] = str(fixture_offline_robot["创建时间"])
    # 测试更新名称
    robot_info = {"机器人": jsonable_encoder(fixture_offline_robot)}
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_offline_robot['标识符']}", json=robot_info, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{fixture_offline_robot['标识符']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["标识符"] == fixture_offline_robot["标识符"]
    assert response.json()["名称"] == "修改啦修改啦哈哈哈"


def test_update_robot_operational(fixture_client, fixture_settings, vip_user_headers, fixture_offline_robot, mocker):
    """更新机器人的运行数据"""
    mocker.patch("app.api.api_v1.endpoints.robot.update_stralib_robot_data", mock_update_stralib_robot_data)
    # 正例
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_offline_robot['标识符']}/operational", headers=vip_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{fixture_offline_robot['标识符']}", headers=vip_user_headers)
    assert response.status_code == 200
    # 状态错误
    db = asyncio.get_event_loop().run_until_complete(get_database())
    result = asyncio.get_event_loop().run_until_complete(get_robots_collection(db).update_one({"标识符": fixture_offline_robot["标识符"]}, {"$set": {"状态": "审核中"}}))
    assert result.matched_count == 1
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_offline_robot['标识符']}/operational", headers=vip_user_headers)
    assert response.status_code == 400
    assert "状态错误" in response.text


def test_query_robot_assess_result(fixture_client, fixture_settings, free_user_headers):
    """查询机器人评估评级信息"""
    test_sid = "10190527bdsz02"
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{test_sid}/assess_result?start=2018-01-01&end=2019-05-30", headers=free_user_headers)
    assert response.status_code == 200
    assert "ann_rate" in response.json()


# ========================回测数据 测试用例
def test_create_robot_backtest_indicator(fixture_client, fixture_settings, fixture_db, event_loop, airflow_user_headers, fixture_online_robot):
    """创建机器人回测指标数据"""
    start = end = get_early_morning().isoformat().split("T")[0]
    robot_backtest_indicator_data["机器人回测指标数据"][0]["标识符"] = fixture_online_robot["标识符"]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_indicator", json=robot_backtest_indicator_data, headers=airflow_user_headers)
    assert response.status_code == 200
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_indicator", json=robot_backtest_indicator_data, headers=airflow_user_headers)
    assert response.status_code == 400
    assert "数据重复写入" in response.json()["message"]
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/backtest_indicator?start={start}&end={end}", headers=airflow_user_headers
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot["标识符"]
    assert len(response.json()) == 1
    event_loop.run_until_complete(get_collection_by_config(fixture_db, "机器人回测指标collection名").delete_many({"标识符": fixture_online_robot["标识符"]}))


def test_get_robot_backtest_indicator(fixture_client, fixture_settings, free_user_headers, fixture_online_robot_backtest_indicator):
    """查询机器人回测指标数据"""
    start = end = get_early_morning().isoformat().split("T")[0]
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_backtest_indicator[0]['标识符']}/backtest_indicator?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot_backtest_indicator[0]["标识符"]
    assert len(response.json()) == 1


def test_create_robot_backtest_signal(fixture_client, fixture_settings, fixture_db, event_loop, airflow_user_headers, fixture_online_robot):
    """创建机器人回测信号"""
    start = end = get_early_morning().isoformat().split("T")[0]
    robot_backtest_signal_data["机器人回测信号数据"][0]["标识符"] = fixture_online_robot["标识符"]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_signal", json=robot_backtest_signal_data, headers=airflow_user_headers)
    assert response.status_code == 200
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_signal", json=robot_backtest_signal_data, headers=airflow_user_headers)
    assert response.status_code == 400
    assert response.json()["message"] == "[10000000test01]数据重复写入."
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/backtest_signal?start={start}&end={end}", headers=airflow_user_headers
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot["标识符"]
    assert len(response.json()) == 1
    db = asyncio.get_event_loop().run_until_complete(get_database())
    asyncio.get_event_loop().run_until_complete(get_collection_by_config(db, "机器人回测信号collection名").delete_many({"标识符": fixture_online_robot["标识符"]}))


def test_get_robot_backtest_signal(fixture_client, fixture_settings, free_user_headers, fixture_online_robot_backtest_signal):
    """查询机器人回测信号"""
    start = end = get_early_morning().isoformat().split("T")[0]
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_backtest_signal[0]['标识符']}/backtest_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot_backtest_signal[0]["标识符"]
    assert len(response.json()) == 1


def test_create_robot_backtest_assess(fixture_client, fixture_settings, fixture_db, event_loop, airflow_user_headers, fixture_online_robot):
    """创建机器人回测评级"""
    for item in robot_backtest_assess_data["机器人回测评级数据"]:
        item["标识符"] = fixture_online_robot["标识符"]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_assess", json=robot_backtest_assess_data, headers=airflow_user_headers)
    assert response.status_code == 200
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_assess", json=robot_backtest_assess_data, headers=airflow_user_headers)
    assert response.status_code == 200
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/backtest_assess", headers=airflow_user_headers)
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot["标识符"]
    assert len(response.json()) == 3
    robot = event_loop.run_until_complete(get_robots_collection(fixture_db).find_one({"标识符": fixture_online_robot["标识符"]}))
    assert robot_backtest_assess_data["机器人回测评级数据"][-1]["评级"] == robot["评级"]
    event_loop.run_until_complete(get_collection_by_config(fixture_db, "机器人回测评级collection名").delete_many({"标识符": fixture_online_robot["标识符"]}))


def test_get_robot_backtest_assess(fixture_client, fixture_settings, free_user_headers, fixture_online_robot_backtest_assess):
    """查询机器人回测评级"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_backtest_assess[0]['标识符']}/backtest_assess", headers=free_user_headers
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot_backtest_assess[0]["标识符"]
    assert len(response.json()) == 3


# ========================实盘数据 测试用例
def test_create_robot_real_indicator(fixture_client, fixture_settings, fixture_db, event_loop, airflow_user_headers, fixture_online_robot):
    """创建机器人实盘指标"""
    start = end = get_early_morning().isoformat().split("T")[0]
    robot_real_indicator_data["机器人实盘指标数据"][0]["标识符"] = fixture_online_robot["标识符"]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/real_indicator", json=robot_real_indicator_data, headers=airflow_user_headers)
    assert response.status_code == 200
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/real_indicator", json=robot_real_indicator_data, headers=airflow_user_headers)
    assert response.status_code == 400
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/real_indicator?start={start}&end={end}", headers=airflow_user_headers
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot["标识符"]
    assert len(response.json()) == 1
    event_loop.run_until_complete(get_collection_by_config(fixture_db, "机器人实盘指标collection名").delete_many({"标识符": fixture_online_robot["标识符"]}))


def test_get_robot_real_indicator(fixture_client, fixture_settings, free_user_headers, fixture_online_robot_real_indicator):
    """查询机器人实盘指标"""
    start = end = get_early_morning().isoformat().split("T")[0]
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_real_indicator[0]['标识符']}/real_indicator?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot_real_indicator[0]["标识符"]
    assert len(response.json()) == 1


def test_get_latest_robot_real_indicator(fixture_client, fixture_settings, fixture_db, event_loop, free_user_headers, fixture_online_robot_real_indicator):
    """查询机器人最新实盘指标数据"""
    # 数据未更新
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_real_indicator[0]['标识符']}/real_indicator/latest", headers=free_user_headers
    )
    assert response.status_code == 400
    assert "[机器人计算时间错误] 不是最新的计算时间" in response.text
    # 上上个交易日上线返回
    上线时间 = FastTdate.last_tdate(FastTdate.last_tdate(get_early_morning()))
    计算时间 = get_early_morning()
    event_loop.run_until_complete(
        get_robots_collection(fixture_db).update_one({"标识符": fixture_online_robot_real_indicator[0]["标识符"]}, {"$set": {"上线时间": 上线时间, "计算时间": 计算时间}})
    )
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_real_indicator[0]['标识符']}/real_indicator/latest", headers=free_user_headers
    )
    assert response.status_code == 200
    assert response.json()["标识符"] == fixture_online_robot_real_indicator[0]["标识符"]


def test_create_robot_real_signal(fixture_client, fixture_settings, fixture_db, event_loop, airflow_user_headers, fixture_online_robot):
    """创建机器人最新实盘信号数据"""
    start = end = get_early_morning().isoformat().split("T")[0]
    robot_real_signal_data["机器人实盘信号数据"][0]["标识符"] = fixture_online_robot["标识符"]
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/real_signal", json=robot_real_signal_data, headers=airflow_user_headers)
    assert response.status_code == 200
    response = fixture_client.post(f"{fixture_settings.url_prefix}/robots/real_signal", json=robot_real_signal_data, headers=airflow_user_headers)
    assert response.status_code == 400
    assert response.json()["message"] == "[10000000test01]数据重复写入."
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/real_signal?start={start}&end={end}", headers=airflow_user_headers
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot["标识符"]
    assert len(response.json()) == 1
    event_loop.run_until_complete(get_collection_by_config(fixture_db, "机器人实盘信号collection名").delete_many({"标识符": fixture_online_robot["标识符"]}))


def test_get_robot_real_signal(fixture_client, fixture_settings, free_user_headers, fixture_online_robot_backtest_signal):
    """查询机器人最新实盘信号数据"""
    start = end = get_early_morning().isoformat().split("T")[0]
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_backtest_signal[0]['标识符']}/backtest_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot_backtest_signal[0]["标识符"]
    assert len(response.json()) == 1


def test_get_latest_robot_real_signal(fixture_client, fixture_settings, free_user_headers, fixture_online_robot_real_signal):
    """查询机器人最新实盘信号数据"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/{fixture_online_robot_real_signal[0]['标识符']}/real_signal/latest", headers=free_user_headers
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == fixture_online_robot_real_signal[0]["标识符"]
    assert datetime.strptime(response.json()[0]["交易日期"], "%Y-%m-%dT%H:%M:%SZ") == get_early_morning()


def test_get_robot_backtest_details(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_online_robot_backtest_indicator,
    fixture_online_robot_backtest_signal,
    fixture_online_robot_backtest_assess,
):
    """查询机器人回测详情"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/backtest/details/{fixture_online_robot_backtest_indicator[0]['标识符']}?数据集=整体评级", headers=free_user_headers
    )
    assert response.status_code == 200
    assert response.json()["机器人回测指标详情"]["标识符"] == fixture_online_robot_backtest_indicator[0]["标识符"]


def test_update_robot_status(fixture_client, fixture_settings, fixture_db, root_user_headers, fixture_online_robot):
    """更新某机器人状态"""
    params = {"操作类型": "我要上线"}
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/action", json=params, headers=root_user_headers)
    assert response.status_code == 422
    assert "value is not a valid enumeration" in response.text
    params = {"操作类型": "下线"}
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/action", json=params, headers=root_user_headers)
    assert response.status_code == 400
    assert "当前机器人被组合使用中，无法下线" in response.text
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ROBOT].update_one({"标识符": fixture_online_robot["标识符"]}, {"$set": {"管理了多少组合": 0}})
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/action", json=params, headers=root_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["状态"] == "已下线"
    params = {"操作类型": "删除"}
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/action", json=params, headers=root_user_headers)
    assert response.status_code == 400
    assert "当前机器人被订阅中，无法删除" in response.text
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ROBOT].update_one({"标识符": fixture_online_robot["标识符"]}, {"$set": {"订阅人数": 0}})
    response = fixture_client.put(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}/action", json=params, headers=root_user_headers)
    assert response.status_code == 200
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/{fixture_online_robot['标识符']}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["状态"] == "已删除"


def test_query_store_robot_list(fixture_client, fixture_settings, vip_user_headers, root_user_headers, vip_user_data, fixture_online_robot):
    """查询商城内的机器人列表"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json() is not None
    params = {"排序": "xxxx"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 422
    params = {"排序": "分析了多少支股票"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"] == sorted(response.json()["数据"], key=lambda x: x["分析了多少支股票"], reverse=True)
    params = {"排序": "累计创造收益"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"] == sorted(response.json()["数据"], key=lambda x: x["累计创造收益"], reverse=True)
    params = {"排序": "运行天数"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"] == sorted(response.json()["数据"], key=lambda x: x["运行天数"], reverse=True)
    params = {"排序": "累计产生信号数"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"] == sorted(response.json()["数据"], key=lambda x: x["累计产生信号数"], reverse=True)
    params = {"排序": "累计服务人数"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"] == sorted(response.json()["数据"], key=lambda x: x["累计服务人数"], reverse=True)
    params = {"排序": "上线时间"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"] == sorted(response.json()["数据"], key=lambda x: x["上线时间"], reverse=True)
    params = {"排序": "订阅人数"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"] == sorted(response.json()["数据"], key=lambda x: x["订阅人数"], reverse=True)
    # 全文搜索
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/store/list?search={fixture_online_robot['名称']}", params=params, headers=vip_user_headers
    )
    assert response.status_code == 200
    assert len(response.json()["数据"]) == 1
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/store/list?search={fixture_online_robot['作者']}", params=params, headers=vip_user_headers
    )
    assert response.status_code == 200
    assert len(response.json()["数据"]) == 1
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/robots/store/list?search={fixture_online_robot['标识符']}", params=params, headers=vip_user_headers
    )
    assert response.status_code == 200
    assert len(response.json()["数据"]) == 1
    # 昵称
    params = {"昵称": "用户" + vip_user_data["user"]["mobile"][-4:]}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["数据"][0]["作者"]["username"] == vip_user_data["user"]["username"]
    # 标签
    params = {"标签": fixture_online_robot["标签"][0]}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/store/list", params=params, headers=vip_user_headers)
    assert response.status_code == 200
    assert params["标签"] in response.json()["数据"][0]["标签"]




def test_create_robot_backtest(fixture_client, fixture_settings, airflow_user_headers, fixture_online_robot):
    """测试创建机器人实盘数据-交易时间是否连续."""
    robot_backtest_indicator_data["机器人回测指标数据"][0]["标识符"] = fixture_online_robot["标识符"]
    day_1, day_2 = datetime.today() - timedelta(days=1), datetime.today() - timedelta(days=7)
    data_base = robot_backtest_indicator_data["机器人回测指标数据"][0]
    data_base_day_1 = data_base.copy()
    data_base_day_2 = data_base.copy()
    data_base_day_1["交易日期"] = get_early_morning(dt=day_1).isoformat()
    data_base_day_2["交易日期"] = get_early_morning(dt=day_2).isoformat()

    data_a = {"机器人回测指标数据": [data_base, data_base_day_2]}
    response_a = fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_indicator", json=data_a, headers=airflow_user_headers)
    assert response_a.status_code == 400
    assert "给定数据的交易日期不连续" in response_a.json()["message"]


def test_recommend_robots(fixture_client, fixture_settings, free_user_headers, mocker):
    # 实盘指标不存在
    mocker.patch("app.crud.robot.get_strategy_data_list", mock_empty_strategy_data_list)
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/recommend/", headers=free_user_headers)
    assert response.status_code == 400
    assert response.json()["code"] == "114007"
    assert response.json()["message"] == "查询机器人实盘指标错误,未查询到存在实盘指标的机器人"
    # 机器人不存在
    mocker.patch("app.crud.robot.get_strategy_data_list", side_effect=mock_get_strategy_data_list)
    mocker.patch("app.crud.robot.get_client_robot_list", mock_empty_client_robot_list)
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/recommend/", headers=free_user_headers)
    assert response.status_code == 400
    assert response.json()["code"] == "114007"
    assert response.json()["message"] == "查询机器人错误, 未查询到符合要求的机器人"
    # 正例
    mocker.patch("app.crud.robot.get_client_robot_list", side_effect=mock_get_client_robot_list)
    response = fixture_client.get(f"{fixture_settings.url_prefix}/robots/recommend/", headers=free_user_headers)
    assert response.status_code == 200
    assert len(response.json()) == 3
