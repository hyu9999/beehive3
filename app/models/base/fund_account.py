from datetime import datetime
from typing import Optional

from pydantic import Field, root_validator

from app.enums.fund_account import CurrencyType, Exchange, FlowTType
from app.models.rwmodel import PyDecimal, RWModel


class FundAccount(RWModel):
    """资金账户."""

    capital: PyDecimal = Field(..., description="初始资金")
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field("0.00", description="证券资产")
    commission: PyDecimal = Field("0.0003", description="佣金")
    tax_rate: PyDecimal = Field("0.001", description="税点")
    slippage: PyDecimal = Field("0.01", description="滑点")
    ts_data_sync_date: datetime = Field(..., description="时点数据同步日期")
    currency: CurrencyType = Field(CurrencyType.CNY, description="币种")

    class Config(RWModel.Config):
        # 验证默认字段
        validate_all = True


class FundAccountFlowMeta(RWModel):
    """资金账户流水."""

    fund_id: str = Field(..., description="资金账户")
    symbol: str = Field(..., description="股票代码")
    exchange: Exchange = Field(..., description="交易所")
    ttype: FlowTType = Field(..., description="流水类别")
    stkeffect: int = Field(..., description="成交数量(正为买入, 负为卖出)")
    cost: PyDecimal = Field(..., description="成本价")
    tdate: datetime = Field(..., description="交易日")
    currency: CurrencyType = Field(CurrencyType.CNY, description="币种")
    ts: Optional[int] = Field(None, description="时间戳")


class FundAccountFlow(FundAccountFlowMeta):
    """资金账户流水."""

    fundeffect: PyDecimal = Field("0.0", description="资金变动(正为买入, 负为卖出)")
    tprice: PyDecimal = Field(..., description="成交价")
    total_fee: PyDecimal = Field("0.0", description="总费用")
    commission: PyDecimal = Field("0.0", description="佣金")
    tax: PyDecimal = Field("0.0", description="印花税")

    class Config(RWModel.Config):
        # 验证默认字段
        validate_all = True


class FundAccountPosition(RWModel):
    """资金账户持仓."""

    fund_id: str = Field(..., description="资金账户")
    symbol: str = Field(..., description="股票代码")
    exchange: Exchange = Field(..., description="交易所")
    volume: int = Field(..., description="持仓量")
    available_volume: int = Field(..., description="可用持仓")
    cost: PyDecimal = Field(..., description="持仓成本")
    first_buy_date: datetime = Field(default_factory=datetime.utcnow, description="首次买入日期")
    count: int = Field(0, title="持有天数")
    current_price: float = Field(0, title="当前价")

    @root_validator(pre=True)
    def set_available_volume(cls, input_data):
        """设置可用持仓数据."""
        available_volume = input_data.get("available_volume")
        if available_volume is None:
            input_data["available_volume"] = input_data["volume"]
        return input_data
