from datetime import datetime, date
from typing import Optional, List

from pydantic import Field, root_validator

from app.enums.fund_account import CurrencyType, FlowTType
from app.models.base.fund_account import FundAccount, FundAccountFlowMeta
from app.models.fund_account import FundAccountPositionInDB
from app.models.rwmodel import PyObjectId, RWModel, PyDecimal


class FundAccountInCreate(FundAccount):
    portfolio_id: PyObjectId = Field(..., description="组合ID")


class FundAccountInUpdate(RWModel):
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    ts_data_sync_date: datetime = Field(..., description="时点数据同步日期")
    securities: PyDecimal = Field(..., description="证券资产")


class FundAccountFlowInUpdate(RWModel):
    ttype: FlowTType = Field(..., description="流水类别")
    stkeffect: int = Field(..., description="成交数量(正为买入, 负为卖出)")
    cost: PyDecimal = Field(..., description="成本价")


class FundAccountFlowInCreate(FundAccountFlowMeta):
    tdate: date = Field(..., description="交易日期")


class DepositOrWithDraw(RWModel):
    """出入金."""
    fund_id: str = Field(..., description="资金账户")
    amount: PyDecimal = Field(..., description="金额")
    tdate: date = Field(..., description="交易日")


class FundAccountPositionInUpdate(RWModel):
    """资金账户持仓更新."""
    volume: int = Field(..., description="持仓量")
    cost: PyDecimal = Field(..., description="持仓成本")
    available_volume: int = Field(..., description="可用持仓")

    @root_validator(pre=True)
    def set_available_volume(cls, input_data):
        """设置可用持仓数据."""
        available_volume = input_data.get("available_volume")
        if available_volume is None:
            input_data["available_volume"] = input_data["volume"]
        return input_data


class FundAccountPositionList(RWModel):
    """资金账户持仓."""
    fund_id: str = Field(..., title="资金账户ID")
    currency: CurrencyType = Field(CurrencyType.CNY, title="货币")
    position_list: Optional[List[FundAccountPositionInDB]] = Field(None, title="持仓列表")
