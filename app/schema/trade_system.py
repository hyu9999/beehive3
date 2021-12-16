from typing import Any

from pydantic import Field

from app.models.rwmodel import RWModel


class TradeInResponse(RWModel):
    """
    交易系统返回值
    """
    msg: str = Field(None, description="信息")
    data: Any = Field(None, description="数据")
    flag: bool = Field(..., description="状态")
