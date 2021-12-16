from app.models.base.target_config import 指标配置基本信息


class TradeStatsConf(指标配置基本信息):
    """交易统计配置表"""


class StockStatsConf(指标配置基本信息):
    """个股统计配置表"""


class PortfolioTargetConf(指标配置基本信息):
    """组合指标配置表"""
