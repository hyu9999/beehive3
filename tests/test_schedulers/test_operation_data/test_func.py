import pytest
from pandas import DataFrame

from app.schedulers.operation_data.func import update_operation_data, update_strategy_calculate_datetime

pytestmark = pytest.mark.asyncio


def test_update_operation_data(mocker):
    """测试同步运行数据方法"""
    # mock掉数据库操作
    mocker.patch("app.schedulers.operation_data.func.get_client_robot_and_equipment", return_value=(["10000000tes000"], ["02200000000001"]))
    mocker.patch("app.schedulers.operation_data.func.Beehive", type("MockBeehive", (), {"query_robot_or_equipment_info": lambda *args, **kwargs: {}}))
    mocker.patch("app.schedulers.operation_data.func.mongo_util", type("MockMongoUtil", (), {"batch_update": lambda *args, **kwargs: {}}))
    error = update_operation_data()
    assert error is None
    # mocker Beehive方法抛出异常
    mocker.patch("app.schedulers.operation_data.func.Beehive", side_effect=Exception())
    error = update_operation_data()
    assert error is None


async def test_update_strategy_calculate_datetime(mocker):
    """测试同步策略计算时间方法"""
    # mock掉数据库操作
    async def mock_get_robot_and_equipment(*args, **kwargs):
        return ["10000000tes000"], ["01000000test01", "02200000test01", "03000000test01", "04000000test01", "11000000test01"]

    mocker.patch("app.schedulers.operation_data.func.get_robot_and_equipment", mock_get_robot_and_equipment)

    class MockConfigCollection(object):
        def __init__(self, *args, **kwargs):
            pass

        async def count_documents(self, *args, **kwargs):
            return 1

        async def find_one(self, *args, **kwargs):
            if "计算时间" in args[0].keys():  # mock计算时间未更新
                return None
            return {"装备列表": ["04000000test01", "04000000test02"]}  # mock查询sid信息

        async def update_one(self, *args, **kwargs):
            return {}

    mocker.patch("app.schedulers.operation_data.func.get_collection_by_config", MockConfigCollection)

    func = lambda strategy_id, start_datetime, end_datetime: DataFrame() if strategy_id == "04000000test01" else DataFrame([1])
    # mock 风控包中信号未全部更新，不更新此风控包
    mocker.patch("app.schedulers.operation_data.func.get_strategy_signal", func)
    error = await update_strategy_calculate_datetime()
    assert isinstance(error, list)
    # mock 风控包中信号全部更新，更新此风控包
    mocker.patch("app.schedulers.operation_data.func.get_strategy_signal", return_value=DataFrame([1]))
    error = await update_strategy_calculate_datetime()
    assert isinstance(error, list)

    class MockConfigCollectionNone(MockConfigCollection):
        async def find_one(self, *args, **kwargs):
            # mock风控包不存在，返回None
            return None

    # mock 风控包不存在，跳过当前循环继续执行
    mocker.patch("app.schedulers.operation_data.func.get_collection_by_config", MockConfigCollectionNone)
    await update_strategy_calculate_datetime()
