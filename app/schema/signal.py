from pydantic import Field, BaseModel, validator, ValidationError
from datetime import date

from typing import List

from app.enums.common import 操作方向
from app.models.base.stock import 股票基本信息
from app.models.equipment import Equipment


class StockSignalInfo(股票基本信息):
    """入选股票信息"""

    chosen_reason: str = Field(None, title="入选理由")
    chosen_price: float = Field(None, title="入选价格")


class ScreenStrategySignalInResponse(BaseModel):
    """选股装备策略信号"""

    signal_date: date = Field(..., title="信号日期")
    equipment: Equipment = Field(..., title="装备信息")
    strategy_signals: List[StockSignalInfo] = Field(..., title="入选股票信号列表")


class TimingStrategySignalInResponse(BaseModel):
    """择时装备策略信号"""

    trade_date: date = Field(..., title="交易日期")
    market_trend: str = Field(..., title="交易趋势")
    position_rate_advice: List[float] = Field(..., title="建议仓位")
    valuation_quantile: float = Field(None, title="估值分位数")


class TradeStrategySignalInfo(BaseModel):
    """个股买卖股票信息"""

    symbol_shortname: str = Field(..., title="股票代码简称")
    trade_date: date = Field(..., title="日期", alias="date")
    price: float = Field(..., title="价格")
    advice: str = Field(..., title="建议")
    title: str = Field(..., title="标题")
    operator: int = Field(..., title="操作方式")
    industry: str = Field(..., title="公司")

    @validator("operator")
    def stralib_operator_convert(cls, v):
        if v == 1:
            return 操作方向.买入
        elif v == -1:
            return 操作方向.卖出
        elif v == 0:
            return 操作方向.保持不变
        else:
            raise ValidationError("value must be member of Enum 操作方向")


class TradeStrategySignalInResponse(BaseModel):
    equipment: Equipment = Field(..., title="装备信息")
    strategy_signals: List[TradeStrategySignalInfo] = Field(..., title="交易装备策略信号列表")
