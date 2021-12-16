from datetime import datetime
from typing import List

from pydantic import Field

from app.models.base.stock import 股票基本信息
from app.models.rwmodel import RWModel, EmbeddedDocument, PyObjectId


class 持仓时点数据(股票基本信息):
    stock_quantity: int = Field(None, title="持仓数量")
    market_value: float = Field(None, title="市值")
    stop_loss: float = Field(0, title="止损价格")
    stop_profit: float = Field(999999, title="止盈价格")
    tdate: datetime = Field(None, title="交易日日期")
    buy_date: datetime = Field(None, title="首次买入日期")
    avg_price: float = Field(None, title="成本价")
    tprice: float = Field(0, title="当前价")
    count: int = Field(0, title="持有天数")
    stock_available_quantity: int = Field(None, title="可用数量")
    float_profit: float = Field(None, title="浮动盈亏")


class 持仓开放基金时点数据(EmbeddedDocument):
    ofcode: str = Field(..., title="基金代码", unique_with=["tacode"])
    tacode: str = Field(..., title="基金公司代码")
    oflastbal: float = Field(..., title="上期余额")
    ofbal: float = Field(..., title="当前余额")
    ofavl: float = Field(..., title="可用份额")
    oftrdfrz: float = Field(..., title="交易冻结份额")
    oflongfrz: float = Field(..., title="长期冻结份额")
    lastcost: float = Field(..., title="上期成本")
    currentcost: float = Field(..., title="当前成本")
    market_value: float = Field(..., title="市值")


class 账户分析数据(EmbeddedDocument):
    asset_distribution: List[str] = Field([], title="资产分布")
    account_yield: float = Field(0, title="收益率")
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


class 时点数据基本信息(RWModel):
    total_capital: float = Field(0, title="总资产")
    market_value: float = Field(0, title="总市值")
    position: float = Field(0, title="仓位")
    fund_available: float = Field(0, title="资金余额")
    fund_balance: float = Field(0, title="可用资金")
    fund_depositable: float = Field(0, title="可取资金")
    stk_asset: List[持仓时点数据] = Field([], title="持仓时点数据")
    of_asset: List[持仓开放基金时点数据] = Field([], title="持仓开放基金时点数据")
    assessment: 账户分析数据 = Field(账户分析数据(), title="账户分析数据")


class 组合时点数据基本信息(时点数据基本信息):
    portfolio: PyObjectId = Field(..., title="组合")
    tdate: datetime = Field(..., title="日期")
