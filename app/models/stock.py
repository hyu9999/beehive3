from pydantic import Field

from app.enums.stock import 股票市场Enum
from app.models.base.stock import 自选股
from app.models.dbmodel import DBModelMixin
from app.models.rwmodel import RWModel, PyObjectId


class FavoriteStock(DBModelMixin, 自选股):
    """自选股表"""


class StockPool(RWModel):
    """组合股票池"""
    portfolio_id: PyObjectId = Field(..., title="组合id")
    group: str = Field("自选股", title="分组", description="需要和组合id建立联合索引")
    symbol: str = Field(..., title="股票代码")
    exchange: 股票市场Enum = Field(..., title="交易所")
    stop_profit: float = Field(9999, title="止盈价")
    stop_loss: float = Field(0, title="止损价")
