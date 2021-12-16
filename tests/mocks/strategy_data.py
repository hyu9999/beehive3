from motor.motor_asyncio import AsyncIOMotorClient
from typing import List

from app.enums.strategy_data import 策略名称, 策略数据类型
from app.schema.common import ResultInResponse
from app.schema.strategy_data import StrategyInCreate
from tests.consts.robots import robot_real_indicator_data, robot_test_data
from tests.fixtures.strategy_data import test_strategy_data


async def mock_创建策略数据(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, strategy_data: List[dict]):
    return ResultInResponse()


async def mock_查询策略数据(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, filters: dict, limit: int, skip: int, sort: list):
    return test_strategy_data[strategy_name][strategy_type]


async def mock_删除策略数据(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, filters: dict):
    return ResultInResponse()


async def mock_get_strategy_data_list(conn: AsyncIOMotorClient, config: str, filters: dict, sort: list = None):
    robot_real_indicator_data["机器人实盘指标数据"][0]["标识符"] = robot_test_data["标识符"]
    return robot_real_indicator_data["机器人实盘指标数据"]


async def mock_empty_strategy_data_list(conn: AsyncIOMotorClient, config: str, filters: dict, sort: list = None):
    return []


async def mock_策略数据完整性检验(conn: AsyncIOMotorClient, strategy_name: 策略名称, strategy_type: 策略数据类型, 策略数据: List[StrategyInCreate]):
    ...
