from datetime import datetime

from pydantic import Field

from app.models.base.operation import 趋势图信息
from app.models.operation import TrendChart


class TrendChartInCreate(趋势图信息):
    pass


class TrendChartInUpdate(趋势图信息):
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrendChartInResponse(TrendChart):
    pass
