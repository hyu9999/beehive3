from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient

from app.schema.equipment import SymbolGradeStrategyWordsInresponse, 装备InResponse
from tests.consts.equipment import 大类资产配置装备基础数据, 基金定投装备基础数据, risk_test_data, timing_test_data


async def mock_get_grade_strategy_words_by_time(*args, **kwargs):
    """mock 查询某段时间内用户的股票池中有风险的股票及对应风控策略话术"""
    return [SymbolGradeStrategyWordsInresponse(**{"symbol": "601515", "grade_strategy_word": [{"grade": "高风险", "strategy_words": "mock"}]})]


@dataclass
class MockEquipmentCollection(object):
    """
    mock get_equipment_collection
    :param conn: 异步数据库连接对象
    :return:
    """

    conn: AsyncIOMotorClient

    async def find_one(self, db_query: dict, **kwargs):
        """
        mock find方法
        :param db_query: 数据库查询条件
        :param kwargs: 其他查询条件，eg:sort limit skip
        :return:
        """
        row = dict()
        if "标识符" in db_query.keys():
            if db_query["标识符"].startswith("06"):
                row = 大类资产配置装备基础数据
            elif db_query["标识符"].startswith("07"):
                row = 基金定投装备基础数据
            elif db_query["标识符"].startswith("04"):
                row = risk_test_data
        return row

    async def bulk_write(self, *args, **kwargs):
        pass


async def mock_nothing(*args):
    pass


async def mock_查询某个装备的详情(conn: AsyncIOMotorClient, sid: str):
    if sid.startswith("06"):
        row = 大类资产配置装备基础数据
    elif sid.startswith("07"):
        row = 基金定投装备基础数据
    elif sid.startswith("04"):
        row = risk_test_data
    elif sid.startswith("03"):
        row = timing_test_data
    else:
        raise
    return 装备InResponse(**row)
