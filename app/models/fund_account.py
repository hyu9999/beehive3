from datetime import date, datetime
from typing import Optional

from pydantic import Field, validator

from app.enums.fund_account import Exchange
from app.models.base.fund_account import (
    FundAccount,
    FundAccountFlow,
    FundAccountPosition,
)
from app.models.dbmodel import DBModelMixin
from app.models.rwmodel import PyDecimal
from app.utils.datetime import date2datetime


class FundAccountInDB(DBModelMixin, FundAccount):
    """资金账户."""


class FundAccountFlowInDB(DBModelMixin, FundAccountFlow):
    """资金账户流水."""

    cost: Optional[PyDecimal] = Field(None, description="成本价")
    tprice: Optional[PyDecimal] = Field(None, description="成交均价")
    symbol: Optional[str] = Field(None, description="股票代码")
    exchange: Optional[Exchange] = Field(None, description="交易所")
    stkeffect: int = Field(0, description="成交数量(正为买入, 负为卖出)")

    @validator("tdate", pre=True)
    def tdate_to_datetime(cls, v):
        if isinstance(v, date):
            return date2datetime(v)
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                ...
        return v

    @validator("exchange", pre=True)
    def set_exchange_default(cls, v):
        if v is None:
            return Exchange.CNSESH
        return v

    @validator("symbol", pre=True)
    def set_symbol_default(cls, v):
        if v is None:
            return "SYMBOL"
        return v


class FundAccountPositionInDB(DBModelMixin, FundAccountPosition):
    """资金账户持仓."""
