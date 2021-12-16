from dataclasses import dataclass
from motor.motor_asyncio import AsyncIOMotorClient

from app.enums.equipment import 装备分类转换
from app.enums.strategy import 策略分类
from tests.consts.equipment import 大类资产配置实盘指标数据, 基金定投实盘指标数据
from tests.fixtures.strategy import fake_strategy_info
from tests.fixtures.strategy_data import test_strategy_data


async def mock_async_cursor(cursor):
    """mock异步cursor对象"""
    for row in cursor:
        yield row


@dataclass
class MockConfigCollection(object):
    """
    mock get_collection_by_config
    :param conn: 异步数据库连接对象
    :param config: 集合配置名
    :return:
    """

    conn: AsyncIOMotorClient
    config: str = None

    def find(self, db_query: dict, **kwargs):
        """
        mock find方法
        :param db_query: 数据库查询条件
        :param kwargs: 其他查询条件，eg:sort limit skip
        :return:
        """
        cursor = []
        if self.config == "大类资产配置实盘指标collection名":
            cursor = [大类资产配置实盘指标数据]
        if self.config == "基金定投实盘指标collection名":
            cursor = [基金定投实盘指标数据]
        return mock_async_cursor(cursor)

    async def find_one(self, db_query: dict, **kwargs):
        row = dict()
        if self.config == "大类资产配置实盘指标collection名":
            row = 大类资产配置实盘指标数据
        elif self.config == "基金定投实盘指标collection名":
            row = 基金定投实盘指标数据
        elif self.config == "选股实盘指标collection名":
            row = test_strategy_data["选股"]["实盘指标"]
        elif self.config == "机器人实盘指标collection名":
            row = test_strategy_data["机器人"]["实盘指标"]
        elif self.config == "装备信息collection名":
            if "标识符" in db_query.keys():
                row = [v for k, v in fake_strategy_info[db_query["标识符"][:2]].items() if v["标识符"] == db_query["标识符"]][0]
            else:
                row = row or fake_strategy_info[装备分类转换.选股][db_query["状态"] if "状态" in db_query.keys() else "已上线"]
        elif self.config == "机器人信息collection名":
            if "标识符" in db_query.keys():
                row = [v for k, v in fake_strategy_info[策略分类.机器人].items() if v["标识符"] == db_query["标识符"]][0]
            else:
                row = fake_strategy_info[策略分类.机器人][db_query["状态"] if "状态" in db_query.keys() else "已上线"]
        return row

    async def bulk_write(self, *args, **kwargs):
        pass

    async def delete_many(self, *args, **kwargs):
        pass
