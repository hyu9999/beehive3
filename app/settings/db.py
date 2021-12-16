from pydantic import Field
from pymongo import ASCENDING, MongoClient

from app.settings import OtherSettings


class Collections(OtherSettings):
    SITE_CONFIG: str  # 配置表
    OBJECT_ACTION: str  #
    USER: str = Field(..., env="USER_COLLECTION")  # 用户
    ROLE: str  # 角色
    PERMISSION: str  # 权限
    USER_MESSAGE: str  # 用户信息
    EQUIPMENT: str  # 装备
    ROBOT: str  # 机器人
    PORTFOLIO: str  # 组合
    TAG: str  # 标签
    PORTFOLIO_ACCOUNT: str  # 组合账户
    ACTIVITY: str  # 活动
    ACTIVITY_YIELD_RANK: str  # 活动组合排行
    ERROR_LOG: str  # 错误日志
    STOCK_LOG: str  # 股票流水
    MESSAGE_CONFIG: str  # 消息配置
    TREND_CHART: str  # 趋势图
    ORDER: str  # 订单
    FAVORITE_STOCK: str  # 自选股
    TRADE_STATS_CONF: str  # 交易统计配置
    STOCK_STATS_CONF: str  # 个股统计配置
    PORTFOLIO_TARGET_CONF: str  # 组合指标配置
    STOCK_POOL: str  # 股票池
    # 交易系统
    STRATEGY_DAILY_LOG: str  # 策略每日日志
    STRATEGY_PUBLISH_LOG: str  # 策略发布日志
    ZVT_DATA_LOG: str  # ZVT数据日志
    ZVT_DATA_LOG_TYPE: str  # ZVT数据日志数据类型
    STOCK: str  # 股票信息
    FUND_ACCOUNT_FLOW: str  # 资金账户流水
    FUND_ACCOUNT: str  # 资金账户
    FUND_ACCOUNT_POSITION: str  # 资金账户持仓
    POSITION_TIME_SERIES_DATA: str  # 持仓时点数据
    FUND_TIME_SERIES_DATA: str  # 资产时点数据
    PORTFOLIO_ASSESSMENT_TIME_SERIES_DATA: str  # 组合评估时点数据
    PORTFOLIO_ANALYSIS: str  # 组合分析数据

    # 回测实盘数据
    BACKTEST_SIGNAL_AIP: str  # 回测信号.大类资产配置
    BACKTEST_SIGNAL_CATEGORIES_OF_ASSETS: str  # 回测信号.基金定投
    BACKTEST_SIGNAL_SCREEN: str  # 回测信号.选股装备
    BACKTEST_SIGNAL_TIMING: str  # 回测信号.择时装备
    BACKTEST_SIGNAL_ROBOT: str  # 回测信号.机器人

    BACKTEST_INDICATOR_AIP: str  # 回测指标.大类资产配置
    BACKTEST_INDICATOR_CATEGORIES_OF_ASSETS: str  # 回测指标.基金定投
    BACKTEST_INDICATOR_SCREEN: str  # 回测指标.选股装备
    BACKTEST_INDICATOR_TIMING: str  # 回测指标.择时装备
    BACKTEST_INDICATOR_ROBOT: str  # 回测指标.机器人

    BACKTEST_ASSESSMENT_AIP: str  # 回测评级.大类资产配置
    BACKTEST_ASSESSMENT_CATEGORIES_OF_ASSETS: str  # 回测评级.基金定投
    BACKTEST_ASSESSMENT_SCREEN: str  # 回测评级.选股装备
    BACKTEST_ASSESSMENT_TIMING: str  # 回测评级.择时装备
    BACKTEST_ASSESSMENT_ROBOT: str  # 回测评级.机器人

    REAL_SIGNAL_AIP: str  # 实盘信号.大类资产配置
    REAL_SIGNAL_CATEGORIES_OF_ASSETS: str  # 实盘信号.基金定投
    REAL_SIGNAL_SCREEN: str  # 实盘信号.选股装备
    REAL_SIGNAL_TIMING: str  # 实盘信号.择时装备
    REAL_SIGNAL_ROBOT: str  # 实盘信号.机器人

    REAL_INDICATOR_AIP: str  # 实盘指标.大类资产配置
    REAL_INDICATOR_CATEGORIES_OF_ASSETS: str  # 实盘指标.基金定投
    REAL_INDICATOR_SCREEN: str  # 实盘指标.选股装备
    REAL_INDICATOR_TIMING: str  # 实盘指标.择时装备
    REAL_INDICATOR_ROBOT: str  # 实盘指标.机器人


class ColIndex(OtherSettings):
    # 集合索引
    ACTIVITY_IDX = [("status", False)]
    ACTIVITY_YIELD_RANK_IDX = [("activity", False), ("portfolio", False)]
    EQUIPMENT_IDX = [("标识符", True), ("状态", False)]
    FAVORITE_STOCK_IDX = [
        ([("username", ASCENDING), ("category", ASCENDING), ("sid", ASCENDING), ("relationship", ASCENDING)], True),
    ]
    ORDER_IDX = [
        ("portfolio", False),
        ("username", False),
        ("order_id", False),
        ("fund_id", False),
    ]
    PERMISSION_IDX = [("role", True)]
    PORTFOLIO_IDX = [
        ("status", False),
        ("robot", False),
        ("username", False),
        ("activity", False),
    ]
    PORTFOLIO_ACCOUNT_IDX = [
        ("portfolio", False),
        ([("portfolio", ASCENDING), ("tdate", ASCENDING)], True),
    ]
    PORTFOLIO_TARGET_CONF_IDX = []
    ROBOT_IDX = [("标识符", True), ("状态", False)]
    ROLE_IDX = [("name", True)]
    SITE_CONFIG_IDX = [
        ("值", True),
        ("配置名称", False),
        ([("配置分类", ASCENDING), ("配置名称", ASCENDING)], True),
    ]
    STOCK_LOG_IDX = [
        ("portfolio", False),
        ([("portfolio", ASCENDING), ("order_id", ASCENDING)], True),
    ]
    STOCK_STATS_CONF_IDX = []
    TAG_IDX = [([("name", ASCENDING), ("category", ASCENDING)], True)]
    TREND_CHART_IDX = [([("category", ASCENDING), ("tdate", ASCENDING)], True)]
    TRADE_STATS_CONF_IDX = []
    USER_IDX = [("username", True), ("mobile", False)]
    USER_MESSAGE_IDX = [
        ("username", False),
        (
            [("username", ASCENDING), ("category", ASCENDING), ("is_read", ASCENDING)],
            False,
        ),
    ]
    ERROR_LOG_IDX = [("category", False)]
    MESSAGE_CONFIG_IDX = [([("title", ASCENDING), ("category", ASCENDING)], True)]
    BACKTEST_ASSESSMENT_AIP_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    BACKTEST_ASSESSMENT_ROBOT_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    BACKTEST_ASSESSMENT_CATEGORIES_OF_ASSETS_IDX = [
        ("标识符", True),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    BACKTEST_ASSESSMENT_SCREEN_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    BACKTEST_ASSESSMENT_TIMING_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    BACKTEST_SIGNAL_AIP_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_SIGNAL_ROBOT_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_SIGNAL_CATEGORIES_OF_ASSETS_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_SIGNAL_SCREEN_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_SIGNAL_TIMING_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_INDICATOR_AIP_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_INDICATOR_ROBOT_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_INDICATOR_CATEGORIES_OF_ASSETS_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    BACKTEST_INDICATOR_SCREEN_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    BACKTEST_INDICATOR_TIMING_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    REAL_SIGNAL_AIP_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_SIGNAL_ROBOT_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_SIGNAL_CATEGORIES_OF_ASSETS_IDX = [
        ("标识符", True),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_SIGNAL_SCREEN_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_SIGNAL_TIMING_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_INDICATOR_AIP_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_INDICATOR_ROBOT_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_INDICATOR_CATEGORIES_OF_ASSETS_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("交易日期", ASCENDING)], True),
    ]
    REAL_INDICATOR_SCREEN_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]
    REAL_INDICATOR_TIMING_IDX = [
        ("标识符", False),
        ([("标识符", ASCENDING), ("开始时间", ASCENDING), ("结束时间", ASCENDING)], True),
    ]


class DbSettings(OtherSettings):

    # 接口的数据库
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_USER: str
    MONGO_PASS: str
    MONGO_AUTHDB: str
    MONGODB_URL: str
    MAX_CONNECTIONS: int  # 最大连接数
    MIN_CONNECTIONS: int  # 最小连接数
    DB_NAME: str  # 接口的数据库
    TEST_DB_NAME: str  # 测试数据库

    def get_client(self):
        return MongoClient(
            self.MONGODB_URL,
            maxPoolSize=self.MAX_CONNECTIONS,
            minPoolSize=self.MAX_CONNECTIONS,
        )


db_idx = ColIndex()
