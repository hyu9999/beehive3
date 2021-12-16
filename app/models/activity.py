from pydantic import Field

from app.models.base.activity import 活动基本信息, 活动总收益排行信息
from app.models.dbmodel import DBModelMixin
from app.models.rwmodel import PyObjectId


class Activity(DBModelMixin, 活动基本信息):
    """活动表"""


class ActivityYieldRank(DBModelMixin, 活动总收益排行信息):
    """活动收益排行表"""

    activity: PyObjectId = Field(..., title="活动")
    portfolio: PyObjectId = Field(..., title="组合")
    portfolio_name: str = Field(None, title="组合名称")
