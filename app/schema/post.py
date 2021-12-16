from datetime import datetime

from pydantic import Field

from app.models.base.post import PostBase
from app.models.rwmodel import RWModel


class PostInResponse(PostBase):
    ...


class PostInCreate(RWModel):
    title: str = Field(None, description="标题", min_length=0, max_length=5000)
    topic_id: int = Field(..., description="主题id")
    raw: str = Field(..., description="内容")
    category: int = Field(None, description="分类id")
    target_recipients: str = Field(None, description="目标收件人")
    reply_to_post_number: int = Field(None, description="回复帖子编号，如果是回复文章本身则不传")
    archetype: str = Field(None, description="原型")
    created_at: datetime = Field(None, description="创建时间")


class LikePost(RWModel):
    id: int = Field(None, description="id")
    post_action_type_id: int = Field(2, description="动作类型id")
    flag_topic: bool = Field(False, description="是否标记主题")


class UnlikePost(RWModel):
    post_action_type_id: int = Field(2, description="动作类型id")
