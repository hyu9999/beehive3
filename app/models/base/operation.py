from pydantic import Field

from app.enums.operation import 趋势图分类
from app.models.rwmodel import RWModel


class 趋势图信息(RWModel):
    category: 趋势图分类 = Field(None, title="分类")
    tdate: str = Field(None, title="交易日期")
    max_drawdown: float = Field(None, title="最大回撤")
    profit_rate: float = Field(None, title="收益率")
