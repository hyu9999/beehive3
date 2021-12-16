from typing import List

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorGridFSBucket

from app import settings
from app.core.config import get
from app.enums.common import 数据库排序


def get_user_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.USER]


def get_user_message_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.USER_MESSAGE]


def get_equipment_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.EQUIPMENT]


def get_robots_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ROBOT]


def get_permissions_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.PERMISSION]


def get_roles_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ROLE]


def get_tags_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.TAG]


def get_trend_chart_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.TREND_CHART]


def get_activity_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ACTIVITY]


def get_activity_yield_rank_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ACTIVITY_YIELD_RANK]


def get_msg_config_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.MESSAGE_CONFIG]


def get_error_log_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ERROR_LOG]


def get_stock_log_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.STOCK_LOG]


def get_portfolio_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.PORTFOLIO]


def get_order_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ORDER]


def get_trade_stats_conf_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.TRADE_STATS_CONF]


def get_stock_stats_conf_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.STOCK_STATS_CONF]


def get_portfolio_target_conf_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.PORTFOLIO_TARGET_CONF]


def get_favorite_stock_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.FAVORITE_STOCK]


def get_stock_pool_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.STOCK_POOL]


def get_gridfs_bucket(conn: AsyncIOMotorClient) -> AsyncIOMotorGridFSBucket:
    """获取gridfs的bucket"""
    return AsyncIOMotorGridFSBucket(conn[settings.db.DB_NAME])


def get_collection_by_config(conn: AsyncIOMotorClient, config: str) -> AsyncIOMotorCollection:
    """从site_configs中获取配置的名称，再返回相应的collection"""
    return conn[settings.db.DB_NAME][get(config)]


def get_strategy_daily_log_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.STRATEGY_DAILY_LOG]


def get_strategy_publish_log_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.STRATEGY_PUBLISH_LOG]


def get_zvt_data_log_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ZVT_DATA_LOG]


def get_zvt_data_log_type_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.ZVT_DATA_LOG_TYPE]


def get_stock_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.STOCK]


def get_fund_account_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT]


def get_fund_account_flow_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT_FLOW]


def get_fund_account_position_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT_POSITION]


def get_position_time_series_data_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.POSITION_TIME_SERIES_DATA]


def get_fund_time_series_data_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.FUND_TIME_SERIES_DATA]


def get_portfolio_assessment_time_series_data_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.PORTFOLIO_ASSESSMENT_TIME_SERIES_DATA]


def get_portfolio_analysis_collection(conn: AsyncIOMotorClient) -> AsyncIOMotorCollection:
    return conn[settings.db.DB_NAME][settings.collections.PORTFOLIO_ANALYSIS]


def format_field_sort(sort_str: str) -> List[List]:
    """
    公共排序方法

    Parameters
    ----------
    sort_str: 排序字符串（-name,username）

    Returns
    -------
    [["name", -1], ["username", 1]]
    """
    sort_list = [[x[1:], 数据库排序.倒序.value] if x.startswith("-") else [x, 数据库排序.正序.value] for x in sort_str.split(",")]
    return sort_list
