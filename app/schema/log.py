from datetime import datetime

from pydantic import Field

from app.enums.log import 买卖方向
from app.models.base.log import 错误日志基本信息, 股票交易日志基本信息, 出入金记录
from app.models.base.stock import 股票基本信息
from app.models.log import ErrorLog, StockLog, TSAssets, TSPosition
from app.models.rwmodel import PyObjectId, RWModel


class ErrorLogInCreate(错误日志基本信息):
    pass


class ErrorLogInUpdate(错误日志基本信息):
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ErrorLogInResponse(ErrorLog):
    pass


class StockLogInCreate(股票交易日志基本信息):
    portfolio: PyObjectId = Field(..., title="组合")


class StockLogInUpdate(股票交易日志基本信息):
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    portfolio: PyObjectId = Field(None, title="组合")


class StockLogInResponse(StockLog):
    pass


class ManualStockInCreate(股票基本信息):
    portfolio: PyObjectId = Field(..., title="组合")
    order_direction: 买卖方向 = Field(None, title="买卖方向")
    trade_date: str = Field(None, title="成交日期")
    trade_time: str = Field(None, title="成交时间")
    trade_price: float = Field(None, gt=0, title="成交价格")
    trade_volume: int = Field(None, gt=0, title="成交数量")


class ManualStockInUpdate(RWModel):
    order_direction: 买卖方向 = Field(None, title="买卖方向")
    trade_price: float = Field(None, gt=0, title="成交价格")
    trade_volume: int = Field(None, gt=0, title="成交数量")


class AssetsInResponse(TSAssets):
    pass


class AssetsInCreate(TSAssets):
    pass


class AssetsInUpdate(TSAssets):
    pass


class PositionInResponse(TSPosition):
    pass


class PositionInCreate(TSPosition):
    pass


class PositionInUpdate(TSPosition):
    pass


class CashLogInCreate(出入金记录):
    pass
