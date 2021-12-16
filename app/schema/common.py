from datetime import datetime, date
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from app.models.rwmodel import RWModel


class StatusInResponse(BaseModel):
    status: bool


class TradeDateInResponse(BaseModel):
    tdate: date


class TradeDaysInResponse(BaseModel):
    交易日列表: Optional[List[datetime]] = Field(None)


class ResultInResponse(BaseModel):
    result: str = "success"


class PageInResponse(RWModel):
    data: List = Field(None, description="数据")
    count: int = Field(None, description="总数")
    skip: int = Field(None, description="开始下标")
    limit: int = Field(None, description="展示条数")


class KeyValueInResponse(BaseModel):
    name: str
    value: Any
