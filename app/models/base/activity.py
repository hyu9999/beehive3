from datetime import datetime
from typing import List

from pydantic import Field

from app.enums.activity import 活动状态
from app.models.rwmodel import RWModel


class 活动基本信息(RWModel):
    name: str = Field(..., title="名称")
    banner: str = Field(None, title="图片", description="保存头像的id，通过此id可单独取出头像的内容")
    detail_img: str = Field(None, title="详情图")
    start_time: datetime = Field(None, title="开始时间")
    end_time: datetime = Field(None, title="结束时间")
    introduction: str = Field(None, title="介绍")
    status: 活动状态 = Field("online", title="活动状态")
    participants: List[str] = Field([], title="参加者")


class 活动总收益排行信息(RWModel):
    profit_rate: float = Field(..., title="总收益")
    rank: int = Field(..., title="排行")
    over_percent: float = Field(..., title="超过人数比例")
