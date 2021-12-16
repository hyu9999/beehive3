from datetime import date
from typing import Optional

from pydantic import Field

from app.models.base.strawman_data import 装备信号数量, 择时装备信号
from app.models.rwmodel import RWModel


class 选股装备信号列表(RWModel):
    TDATE: date = Field(..., alias="信号日期")
    EXCHANGE: str = Field(..., alias="交易所")
    SYMBOL: str = Field(..., alias="股票代码", description="空值表示当天没有信号")
    SYMBOL_NAME: Optional[str] = Field(None, alias="股票名称", description="空值表示当天没有信号")
    TCLOSE: float = Field(0, alias="入选价格")
    REALTIME_PRICE: Optional[float] = Field(None, alias="现价")


class 择时装备信号列表(择时装备信号):
    指数: str


class 风控装备信号列表(RWModel):
    tdate: date = Field(..., alias="信号日期", description="空值表示当天没有信号")
    symbol: str = Field(..., alias="股票代码", description="空值表示当天没有信号")
    symbol_name: Optional[str] = Field(None, alias="股票名称", description="空值表示当天没有信号")
    exchange: str = Field(None, alias="交易所")
    realtime_price: Optional[float] = Field(None, alias="现价")


class 风控装备信号数量(装备信号数量):
    装备名称: str
