import os

from fastapi import UploadFile
from pytest import fixture, mark

from app.models.rwmodel import PyObjectId
from app.db.mongodb import get_database
from app.crud.file import upload, delete
from tests.consts.robots import (
    robot_test_data,
    robot_backtest_assess_data,
    robot_backtest_signal_data,
    robot_backtest_indicator_data,
    robot_real_indicator_data,
    robot_real_signal_data)


@mark.asyncio
@fixture
async def fixture_pic(fixture_settings):
    """测试图片"""
    db = await get_database()
    with open("test__hello.png", "wb") as f:
        f.write(b"i am a pic")
    file = open("test__hello.png", "rb")
    upload_file = UploadFile("测试图片", file=file, content_type="image/png")
    file_id = await upload(db, "测试图片", upload_file)
    yield file_id
    file.close()
    os.remove("test__hello.png")
    await delete(db, file_id)


@fixture
def fixture_robot_data_in_db(fixture_settings, fixture_db, root_user_data, fixture_pic):
    """已上线机器人数据"""
    online_robot_data = robot_test_data.copy()
    online_robot_data["标识符"] = "10000000test01"
    online_robot_data["作者"] = root_user_data["user"]["username"]
    online_robot_data["名称"] = "test_online_robot"
    online_robot_data["头像"] = str(fixture_pic)
    online_robot_data["_id"] = PyObjectId()
    yield online_robot_data
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ROBOT].delete_many({"标识符": online_robot_data["标识符"]})


@fixture
def fixture_online_robot(fixture_settings, fixture_db, fixture_robot_data_in_db):
    """已上线机器人"""
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ROBOT].insert_one(fixture_robot_data_in_db)
    yield fixture_robot_data_in_db
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ROBOT].delete_many({"标识符": fixture_robot_data_in_db["标识符"]})


@fixture
def fixture_offline_robot(fixture_client, fixture_settings, fixture_db):
    """已下线机器人"""
    offline_robot_data = robot_test_data.copy()
    offline_robot_data["标识符"] = "10000000test02"
    offline_robot_data["状态"] = "已下线"
    offline_robot_data["名称"] = "test_off_line_robot"
    offline_robot_data["_id"] = PyObjectId()
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ROBOT].insert_one(offline_robot_data)
    yield offline_robot_data
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ROBOT].delete_one({"标识符": offline_robot_data["标识符"]})


@fixture
def fixture_online_robot_backtest_indicator(fixture_client, fixture_settings, fixture_db, root_user_headers, fixture_online_robot):
    """机器人回测指标数据"""
    robot_backtest_indicator_data["机器人回测指标数据"][0]["标识符"] = fixture_online_robot["标识符"]
    fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_indicator", json=robot_backtest_indicator_data, headers=root_user_headers)
    yield robot_backtest_indicator_data["机器人回测指标数据"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_INDICATOR_ROBOT].delete_many({"标识符": fixture_online_robot["标识符"]})


@fixture
def fixture_online_robot_backtest_signal(fixture_client, fixture_settings, fixture_db, root_user_headers, fixture_online_robot):
    """机器人回测信号数据"""
    robot_backtest_signal_data["机器人回测信号数据"][0]["标识符"] = fixture_online_robot["标识符"]
    fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_signal", json=robot_backtest_signal_data, headers=root_user_headers)
    yield robot_backtest_signal_data["机器人回测信号数据"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_SIGNAL_ROBOT].delete_many({"标识符": fixture_online_robot["标识符"]})


@fixture
def fixture_online_robot_backtest_assess(fixture_client, fixture_settings, fixture_db, root_user_headers, fixture_online_robot):
    """机器人回测评级数据"""
    for item in robot_backtest_assess_data["机器人回测评级数据"]:
        item["标识符"] = fixture_online_robot["标识符"]
    fixture_client.post(f"{fixture_settings.url_prefix}/robots/backtest_assess", json=robot_backtest_assess_data, headers=root_user_headers)
    yield robot_backtest_assess_data["机器人回测评级数据"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_ASSESSMENT_ROBOT].delete_many({"标识符": fixture_online_robot["标识符"]})


@fixture
def fixture_online_robot_real_indicator(fixture_client, fixture_settings, fixture_db, root_user_headers, fixture_online_robot):
    """机器人实盘指标数据"""
    robot_real_indicator_data["机器人实盘指标数据"][0]["标识符"] = fixture_online_robot["标识符"]
    fixture_client.post(f"{fixture_settings.url_prefix}/robots/real_indicator", json=robot_real_indicator_data, headers=root_user_headers)
    yield robot_real_indicator_data["机器人实盘指标数据"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_INDICATOR_ROBOT].delete_many({"标识符": fixture_online_robot["标识符"]})


@fixture
def fixture_online_robot_real_signal(fixture_client, fixture_settings, fixture_db, root_user_headers, fixture_online_robot):
    """机器人实盘信号数据"""
    robot_real_signal_data["机器人实盘信号数据"][0]["标识符"] = fixture_online_robot["标识符"]
    fixture_client.post(f"{fixture_settings.url_prefix}/robots/real_signal", json=robot_real_signal_data, headers=root_user_headers)
    yield robot_real_signal_data["机器人实盘信号数据"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_SIGNAL_ROBOT].delete_many({"标识符": fixture_online_robot["标识符"]})
