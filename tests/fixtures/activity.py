from datetime import datetime

from pytest import fixture, mark

from app.db.mongodb import get_database
from app.models.rwmodel import PyObjectId

pytestmark = mark.asyncio


@fixture
def activity_data_in_create(fixture_settings, fixture_db):
    """活动创建基础数据"""
    yield {
        "activity": {
            "name": "test_create_activity",
            "banner": "string",
            "detail_img": "string",
            "start_time": datetime(2020, 9, 1),
            "end_time": datetime(2020, 9, 2),
            "introduction": "test",
        }
    }
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ACTIVITY].delete_many({"name": {"$regex": "^test"}})


@fixture
def activity_data_in_db():
    """活动基础数据"""
    return {
        "_id": PyObjectId(),
        "name": "test1",
        "banner": "string",
        "detail_img": "string",
        "start_time": datetime.strptime("2020-09-01", "%Y-%m-%d"),
        "end_time": datetime.strptime("2020-09-01", "%Y-%m-%d"),
        "introduction": "test",
        "status": "online",
        "created_at": datetime.strptime("2020-09-01", "%Y-%m-%d"),
        "updated_at": datetime.strptime("2020-09-01", "%Y-%m-%d"),
        "participants": [],
    }


@fixture
async def fixture_activity(fixture_client, fixture_settings, activity_data_in_db):
    """创建活动，返回活动详情，测试结束清除活动相关测试数据"""
    db = await get_database()
    activity = await _create_activity(db, fixture_settings, activity_data_in_db)
    yield activity
    await _delete_activity(db, fixture_settings, activity_data_in_db["_id"])


async def _create_activity(db, fixture_settings, data):
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.ACTIVITY].insert_one(data)
    return data


async def _delete_activity(db, fixture_settings, activity_id: PyObjectId):
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.ACTIVITY].delete_many({"_id": activity_id})


@fixture
def activity_yield_rank_in_create_data(fixture_db, fixture_settings, fixture_activity, fixture_portfolio):
    """活动排行创建基础数据"""
    yield {
        "activity_yield_rank": {
            "activity": str(fixture_activity["_id"]),
            "portfolio": fixture_portfolio["_id"],
            "portfolio_name": fixture_portfolio["name"],
            "profit_rate": 0.99,
            "rank": 1,
            "over_percent": 1.0,
        }
    }
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ACTIVITY_YIELD_RANK].delete_many({"activity": fixture_activity["_id"]})
