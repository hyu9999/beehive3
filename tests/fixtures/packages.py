from tests.fixtures.equipment import *


@fixture
def test_risk_package_data(test_logined_user):
    data = {
        "名称": "test_风控包",
        "分类": "风控包",
        "作者": test_logined_user["user"]["username"],
        "标识符": "11999999000001",
        "标签": ["移动平均线", "技术指标"],
        "英文名": "TEST_screen",
        "简介": "对均线和成交量进行评",
        "主页地址": "http://bbs.jinniuai.com",
        "可见模式": "完全公开",
        "装备列表": ["04181114dqzs01", "04181114kthq01"],
    }
    return data


@fixture
def test_risk_package(test_risk_equipments, test_settings, test_risk_package_data):
    db = asyncio.get_event_loop().run_until_complete(get_database())
    result = asyncio.get_event_loop().run_until_complete(
        db[test_settings.db.DB_NAME][test_settings.collections.EQUIPMENT].find_one({"标识符": test_risk_package_data["标识符"]})
    )
    if not result:
        asyncio.get_event_loop().run_until_complete(db[test_settings.db.DB_NAME][test_settings.collections.EQUIPMENT].insert_one(test_risk_package_data))
    yield test_risk_package_data
    asyncio.get_event_loop().run_until_complete(db[test_settings.db.DB_NAME][test_settings.collections.EQUIPMENT].delete_many({"名称": {"$regex": "^test"}}))
