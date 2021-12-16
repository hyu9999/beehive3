from datetime import date, datetime
from typing import List, Optional, Set

from pydantic import Field

from app.enums.portfolio import PortfolioCategory, 投资类型, 风险点状态
from app.models.base.portfolio import 用户资金账户信息, 组合基本信息, 组合机器人配置, 组合配置
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId, RWModel


class PortfolioInCreate(RWModel):
    name: str = Field(..., min_length=3, max_length=20, title="名称")
    initial_funding: float = Field(..., ge=10 ** 4, le=10 ** 9, title="初始资金")
    invest_type: 投资类型 = Field("stock", title="投资类型")
    category: PortfolioCategory = Field(
        PortfolioCategory.SimulatedTrading, description="组合类型"
    )
    tags: Set[str] = Field(..., min_items=1, max_items=10, title="标签")
    introduction: str = Field("", title="组合介绍")
    config: 组合配置 = Field(..., title="组合配置")
    robot_config: 组合机器人配置 = Field(..., title="机器人原则")
    robot: str = Field(
        ...,
        max_length=14,
        min_length=14,
        regex=r"^(10|15)[\d]{6}[\w]{4}[\d]{2}$",
        title="机器人标识符",
    )
    is_open: bool = Field(True, title="是否开放")
    activity: PyObjectId = Field(None, title="活动id")


class PortfolioInUpdate(组合基本信息):
    username: str = Field(None, title="用户")
    fund_account: List[用户资金账户信息] = Field(None, title="用户资金账户")
    initial_funding: float = Field(None, title="初始资金")
    robot: str = Field(None, title="机器人")
    close_date: datetime = Field(None, title="结束时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, title="更新时间")


class PortfolioYieldInResponse(RWModel):
    name: str = Field(None, title="组合名称")
    portfolio_id: PyObjectId = Field(None, title="组合id")
    rank: int = Field(None, title="排名")
    over_percent: float = Field(None, title="超越人数")
    profit_rate: float = Field(None, title="收益率")


class PortfolioInResponse(Portfolio):
    pass


class PortfolioBasicRunDataInResponse(RWModel):
    """组合基本运行情况"""

    portfolio: PortfolioInResponse = Field(..., title="组合详情")
    profit_rate: float = Field(..., title="总收益率")
    daily_profit_rate: float = Field(..., title="日收益率")
    weekly_profit_rate: float = Field(..., title="周收益率")
    monthly_profit_rate: float = Field(..., title="月收益率")
    expected_profit_rate: float = Field(..., title="预期收益率")
    expected_reach_date: Optional[date] = Field(None, title="预期达成时间")
    trade_date: date = Field(..., title="交易日期")


class PortfolioRiskStatusInUpdate(RWModel):
    """组合风险点状态更新"""

    id: PyObjectId = Field(..., title="风险点id")
    status: 风险点状态 = Field(..., title="风险点状态")


class PortfolioFundCashInUpdate(RWModel):
    """组合资金账户可用现金更新"""

    cash: float = Field(..., title="可用现金")
