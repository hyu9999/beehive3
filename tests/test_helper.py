import random
import string
from copy import deepcopy

from motor.motor_asyncio import AsyncIOMotorClient

from app.settings.base import GlobalConfig
from scripts.init_db import main as init_db
from tests.consts.equipment import (
    package_test_data,
    risk_test_data,
    screen_test_data,
    timing_test_data,
    trade_test_data,
)
from tests.consts.robots import robot_test_data, const_robot
from tests.consts.stock_stats import stock_stats_data
from tests.consts.target_conf import target_conf_data
from tests.consts.trade_stats import trade_stats_data
from tests.fixtures.strategy import fake_strategy_info


def get_test_db(settings: GlobalConfig) -> str:
    """获取测试DB."""
    db = settings.db.TEST_DB_NAME
    return db


async def init_test_db(
    settings: GlobalConfig, conn: AsyncIOMotorClient, username: str
) -> None:
    """初始化测试DB基础数据."""
    test_db_name = get_test_db(settings)
    await init_db(test_db_name)
    # 为基础数据写入username
    for data in [
        screen_test_data,
        timing_test_data,
        risk_test_data,
        trade_test_data,
        package_test_data,
        robot_test_data,
    ]:
        data["作者"] = username

    # 写入装备基础数据
    await conn[test_db_name][settings.collections.EQUIPMENT].insert_many(
        [
            screen_test_data,
            timing_test_data,
            risk_test_data,
            trade_test_data,
            package_test_data,
        ]
    )
    # 写入机器人基础数据
    await conn[test_db_name][settings.collections.ROBOT].insert_one(robot_test_data)
    for data in const_robot.values():
        data["作者"] = username
        await conn[test_db_name][settings.collections.ROBOT].insert_one(data)
    # 写入交易统计配置数据
    await conn[test_db_name][settings.collections.TRADE_STATS_CONF].insert_many(
        trade_stats_data
    )
    # 组合指标数据
    await conn[test_db_name][settings.collections.PORTFOLIO_TARGET_CONF].insert_many(
        target_conf_data
    )
    # 个股统计
    await conn[test_db_name][settings.collections.STOCK_STATS_CONF].insert_many(
        stock_stats_data
    )
    #
    strategy_info = deepcopy(fake_strategy_info)
    for k, v in strategy_info.items():
        v["已上线"]["作者"] = username
        print(v["已上线"])
        if v["已上线"]["标识符"].startswith("10"):
            await conn[test_db_name][settings.collections.ROBOT].insert_one(v["已上线"])
        else:
            await conn[test_db_name][settings.collections.EQUIPMENT].insert_one(v["已上线"])



async def drop_test_db(settings: GlobalConfig, db: AsyncIOMotorClient) -> None:
    """删除测试数据。"""
    test_db_name = get_test_db(settings)
    db.drop_database(test_db_name)


def get_header(settings: GlobalConfig, logined_user: dict):
    """拼装Authorization Header"""
    return {
        "Authorization": " ".join(
            [settings.auth.jwt_token_prefix, logined_user["token"]]
        )
    }


def get_random_str(str_len: int = 8) -> str:
    return "".join([random.choice(string.ascii_lowercase) for _ in range(str_len)])


async def mock_async_func(*args, **kwargs):
    ...
