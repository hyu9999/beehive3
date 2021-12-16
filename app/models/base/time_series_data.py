from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.enums.fund_account import Exchange
from app.models.rwmodel import PyDecimal, PyObjectId, RWModel


class Position(RWModel):
    """持仓."""

    symbol: str = Field(..., description="股票代码")
    market: Exchange = Field(..., description="交易所")
    stkbal: int = Field(..., description="证券余额")
    mktval: PyDecimal = Field(..., description="证券市值")
    buy_date: Optional[datetime] = Field(None, description="首次买入日期")


class PositionTimeSeriesData(RWModel):
    """持仓时点数据."""

    fund_id: str = Field(..., description="资金账户")
    tdate: datetime = Field(..., description="交易日")
    position_list: Optional[List[Position]] = Field(None, description="持仓列表")


class FundTimeSeriesData(RWModel):
    """资产时点数据."""

    fund_id: str = Field(..., description="资金账户")
    tdate: datetime = Field(..., description="交易日")
    fundbal: PyDecimal = Field(..., description="资金余额")
    mktval: PyDecimal = Field(..., description="证券市值")


class PortfolioAssessmentTimeSeriesData(RWModel):
    """组合评估时点数据."""

    portfolio: PyObjectId = Field(..., title="组合")
    tdate: datetime = Field(..., description="交易日")
    asset_distribution: List[str] = Field([], title="资产分布")
    account_yield: float = Field(0, title="累计收益率")
    weighted_average_cost: float = Field(0, title="加权平均资金成本")
    accumulated_gain: float = Field(0, title="累计盈亏")
    max_drawdown: float = Field(0, title="最大回撤")
    sharpe_ratio: float = Field(0, title="夏普比率")
    mktval_volatility: float = Field(0, title="收益波动率")
    turnover_rate: float = Field(0, title="资金周转率")
    profit_loss_ratio: float = Field(0, title="盈亏比")
    trade_cost: float = Field(0, title="交易成本")
    total_trade_cost: float = Field(0, title="累计交易成本")
    winning_rate: float = Field(0, title="交易胜率")
    abnormal_yield: float = Field(0, title="超额收益率")
    annual_rate: float = Field(0, title="年化收益率")
    stock_industry_distribution: List[str] = Field([], title="股票行业分布")
    openfund_type_distribution: List[str] = Field([], title="基金类别分布")
