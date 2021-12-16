from pytest import fixture

from app.models.rwmodel import PyObjectId


@fixture
def tag_in_create_data(fixture_db, fixture_settings):
    """标签创建数据"""
    tag_name_list = ["test_01", "test_02"]
    yield ["test_01", "test_02"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.TAG].delete_many({"name": {"$regex": "^test"}})


@fixture
def tag_in_db_data(fixture_db, fixture_settings):
    """标签数据库数据"""
    tag_data_list = [{"_id": PyObjectId(), "name": "test_03", "category": "装备"}, {"_id": PyObjectId(), "name": "test_04", "category": "机器人"}]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.TAG].insert_many(tag_data_list)
    yield tag_data_list
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.TAG].delete_many({"name": {"$regex": "^test"}})
