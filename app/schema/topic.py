from datetime import datetime

from pydantic import Field

from app.models.rwmodel import RWModel
from app.models.topic import Topic


class TopicInResponse(Topic):
    ...


class TopicInCreate(RWModel):
    title: str = Field(None, description="标题", min_length=0, max_length=5000)
    topic_id: int = Field(None, description="主题id")
    raw: str = Field(..., description="内容")
    category: int = Field(None, description="分类id")
    target_recipients: str = Field(None, description="目标收件人")
    archetype: str = Field(None, description="原型")
    created_at: datetime = Field(None, description="创建时间")


class TopicInUpdate(RWModel):
    title: str = Field(None, description="标题")
    category_id: int = Field(None, description="分类id")


class BookmarkTopicInUpdate(RWModel):
    reminder_type: int = Field(None, description="提醒类型")
    reminder_at: datetime = Field(None, description="提醒时间")
    name: str = Field(None, description="名称")
    post_id: int = Field(None, description="帖子id")
    delete_when_reminder_sent: bool = Field(False, description="发送提醒时是否删除")
