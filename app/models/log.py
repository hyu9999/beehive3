from pydantic import Field

from app.models.base.log import 股票交易日志基本信息, 错误日志基本信息, 资金账户基本信息, 账户持仓基本信息, 出入金记录
from app.models.dbmodel import DBModelMixin
from app.models.rwmodel import PyObjectId


class ErrorLog(DBModelMixin, 错误日志基本信息):
    """错误信息日志"""


class StockLog(DBModelMixin, 股票交易日志基本信息):
    """股票交易日志"""

    portfolio: PyObjectId = Field(..., title="组合")
    position_change: float = Field(None, title="仓位变化")


class TSAssets(DBModelMixin, 资金账户基本信息):
    """交易系统资金账户"""

    portfolio: PyObjectId = Field(..., description="组合")


class TSPosition(DBModelMixin, 账户持仓基本信息):
    """交易系统账户持仓"""

    portfolio: PyObjectId = Field(..., title="组合")


class CashLog(DBModelMixin, 出入金记录):
    """出入金记录"""
    portfolio: PyObjectId = Field(..., title="组合")
