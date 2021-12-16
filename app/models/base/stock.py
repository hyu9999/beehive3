from typing import List

from pydantic import Field

from app.enums.stock import 股票市场Enum, 自选股分类
from app.models.rwmodel import RWModel


class 股票基本信息(RWModel):
    symbol: str = Field(..., title="股票代码")
    exchange: 股票市场Enum = Field(..., title="股票市场")
    symbol_name: str = Field(None, title="股票名称")


class 股票扩展信息(RWModel):
    symbol_shortname: str = Field(..., title="股票简称")
    industry: str = Field(..., title="行业")


class 股票行情(RWModel):
    previous_close_price: float = Field(..., title="上个交易日收盘价")
    opening_price: float = Field(..., title="开盘价")
    today_low: float = Field(..., title="当日最低价")
    today_high: float = Field(..., title="当日最高价")
    realtime_price: float = Field(..., title="实时价格")


class 自选股股票(RWModel):
    symbol: str = Field(..., title="股票代码")
    exchange: 股票市场Enum = Field(..., title="交易所")
    share_cost_price: float = Field(None, title="成本价")
    stop_profit: float = Field(9999, title="止盈价")
    stop_loss: float = Field(0, title="止损价")


class 自选股(RWModel):
    username: str = Field(..., title="用户")
    category: 自选股分类 = Field("portfolio", title="分类")
    sid: str = Field(None, title="标识符")
    stocks: List[自选股股票] = Field([], title="自选股列表")
    relationship: List = Field(None, title="关联关系")
