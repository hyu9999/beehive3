from pytest import fixture, mark

from app.enums.publish import 策略分类enum, 发布情况enum
from app.models.publish import StrategyPublishLogInDB, StrategyDailyLogInDB
from app.service.datetime import get_early_morning

pytestmark = mark.asyncio


@fixture
def test_strategy_publish_log_data(free_user_data):
    """发布日志数据."""
    data = {
        "username": free_user_data["user"]["username"],
        "交易日期": get_early_morning(),
        "总共发布策略数量": 10,
        "当日发布策略数量": 10,
        "报错策略数量": 1,
        "成功策略数量": 9,
        "已上线策略数量": 10,
        "已下线策略数量": 1,
        "是否完成发布": True
    }
    return data


@fixture
def test_strategy_daily_log_data(fixture_robot_data_in_db):
    """策略每日日志."""
    data = {
        "分类": 策略分类enum.机器人,
        "标识符": fixture_robot_data_in_db["标识符"],
        "交易日期": get_early_morning(),
        "发布情况": 发布情况enum.success,
        "错误信息": []
    }
    return data


@fixture
async def test_strategy_publish_log(test_strategy_publish_log_data, fixture_db, fixture_settings):
    strategy_publish_log_in_db = StrategyPublishLogInDB(**test_strategy_publish_log_data)
    row = await fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.STRATEGY_PUBLISH_LOG].insert_one(
        strategy_publish_log_in_db.dict(exclude={"id"}))
    strategy_publish_log_in_db.id = row.inserted_id
    yield strategy_publish_log_in_db
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.STRATEGY_PUBLISH_LOG].\
        delete_one({"_id": strategy_publish_log_in_db.id})


@fixture
async def test_strategy_daily_log(test_strategy_daily_log_data, fixture_db, fixture_settings):
    strategy_daily_log_in_db = StrategyDailyLogInDB(**test_strategy_daily_log_data)
    row = await fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.STRATEGY_DAILY_LOG].insert_one(
        strategy_daily_log_in_db.dict(exclude={"id"}))
    strategy_daily_log_in_db.id = row.inserted_id
    yield strategy_daily_log_in_db
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.STRATEGY_DAILY_LOG].\
        delete_one({"_id": strategy_daily_log_in_db.id})


def test_get_manufacturer_logs(fixture_client, fixture_settings, free_user_headers, test_strategy_publish_log):
    response = fixture_client.get(f"{fixture_settings.url_prefix}/publish/manufacturer/log", headers=free_user_headers)
    assert response.status_code == 200
    tdate = get_early_morning().date()
    response_1 = fixture_client.get(f"{fixture_settings.url_prefix}/publish/manufacturer/log?开始时间={tdate}&"
                                    f"结束时间={tdate}", headers=free_user_headers)
    assert response_1.status_code == 200
    assert str(test_strategy_publish_log.id) in [log["_id"] for log in response_1.json()]
    response_2 = fixture_client.get(f"{fixture_settings.url_prefix}/publish/manufacturer/log?是否完成发布=false",
                                    headers=free_user_headers)
    assert response_2.status_code == 200
    assert str(test_strategy_publish_log.id) not in [log["_id"] for log in response_2.json()]


def test_get_daily_logs(
    fixture_client,
    fixture_settings,
    free_user_headers,
    test_strategy_daily_log,
):
    response = fixture_client.get(f"{fixture_settings.url_prefix}/publish/strategy/log", headers=free_user_headers)
    assert response.status_code == 200
    assert str(test_strategy_daily_log.id) in [log["_id"] for log in response.json()]


def test_get_daily_log(
    fixture_client,
    fixture_settings,
    free_user_headers,
    test_strategy_daily_log,
):
    response = fixture_client.get(f"{fixture_settings.url_prefix}/publish/strategy/log/{test_strategy_daily_log.标识符}",
                                  headers=free_user_headers)
    assert response.status_code == 200
