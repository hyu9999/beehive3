from datetime import datetime, date

from pydantic import Field

from app.enums.common import 数据库操作Enum
from app.models.base.stock import 股票扩展信息, 股票基本信息, 股票行情, 自选股
from app.models.rwmodel import RWModel
from app.models.stock import FavoriteStock, StockPool


class 股票InResponse(股票扩展信息, 股票基本信息):
    pass


class 股票行情InResponse(股票行情, 股票基本信息):
    pass


class FavoriteStockInCreate(自选股):
    username: str = Field(None, title="用户")


class FavoriteStockInUpdate(自选股):
    username: str = Field(None, title="用户")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FavoriteStockInResponse(FavoriteStock):
    pass


class StockBasicInResponse(股票基本信息):
    """
    股票基本信息（无行业信息）
    """

    symbol_shortname: str = Field(..., title="股票简称")


class MarketIndexDataInResponse(RWModel):
    """
    市场指数的时间戳数据
    """

    时间戳: date = Field(None, title="时间戳")
    开盘价: float = Field(None, title="开盘价")
    最高价: float = Field(None, title="最高价")
    最低价: float = Field(None, title="最低价")
    收盘价: float = Field(None, title="收盘价")
    成交量: float = Field(None, title="成交量")


class StockPoolInCreate(StockPool):
    operator: 数据库操作Enum = Field(None, title="操作类型")


class StockPoolInUpdate(StockPool):
    pass


class StockPoolInResponse(StockPool):
    pass
