from datetime import datetime

from pydantic import Field, BaseModel

from app.models.activity import Activity, ActivityYieldRank
from app.models.base.activity import 活动基本信息, 活动总收益排行信息
from app.models.rwmodel import PyObjectId


class ActivityInCreate(BaseModel):
    name: str = Field(..., title="名称")
    banner: str = Field(None, title="图片", description="保存头像的id，通过此id可单独取出头像的内容")
    detail_img: str = Field(None, title="详情图")
    start_time: datetime = Field(..., title="开始时间")
    end_time: datetime = Field(..., title="结束时间")
    introduction: str = Field(None, title="介绍")


class ActivityInResponse(Activity):
    pass


class ActivityInUpdate(活动基本信息):
    name: str = Field(None, title="名称")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityYieldRankInCreate(活动总收益排行信息):
    activity: PyObjectId = Field(..., title="活动")
    portfolio: PyObjectId = Field(..., title="组合")
    portfolio_name: str = Field(None, title="组合名称")


class ActivityYieldRankInResponse(ActivityYieldRank):
    pass


class ActivityYieldRankInUpdate(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    profit_rate: float = Field(None, title="总收益")
    rank: int = Field(None, title="排行")
    over_percent: float = Field(None, title="超过人数比例")
    activity: PyObjectId = Field(None, title="活动")
    portfolio: PyObjectId = Field(None, title="组合")
    portfolio_name: str = Field(None, title="组合名称")
