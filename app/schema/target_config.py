from pydantic import Field

from app.models.base.target_config import 指标配置基本信息
from app.models.target_config import TradeStatsConf, StockStatsConf, PortfolioTargetConf


class TradeStatsConfInCreate(指标配置基本信息):
    pass


class TradeStatsConfInResponse(TradeStatsConf):
    pass


class TradeStatsConfInUpdate(指标配置基本信息):
    name: str = Field(None, title="名称")
    code: str = Field(None, title="编码")


class StockStatsConfInCreate(指标配置基本信息):
    pass


class StockStatsConfInResponse(StockStatsConf):
    pass


class StockStatsConfInUpdate(指标配置基本信息):
    name: str = Field(None, title="名称")
    code: str = Field(None, title="编码")


class PortfolioTargetConfInCreate(指标配置基本信息):
    pass


class PortfolioTargetConfInResponse(PortfolioTargetConf):
    pass


class PortfolioTargetConfInUpdate(指标配置基本信息):
    name: str = Field(None, title="名称")
    code: str = Field(None, title="编码")
