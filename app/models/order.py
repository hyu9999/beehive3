from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.models.base.order import 股票订单基本信息
from app.models.dbmodel import DBModelMixin
from app.models.rwmodel import PyObjectId


class Order(DBModelMixin, 股票订单基本信息):
    """委托订单"""

    username: str = Field(None, title="用户")
    task: Any = Field(None, title="任务 id")
    portfolio: PyObjectId = Field(..., title="组合")
    create_datetime: datetime = Field(default_factory=datetime.utcnow, title="订单创建时间")
    end_datetime: Optional[datetime] = Field(
        default_factory=datetime.utcnow, title="订单结束时间"
    )
