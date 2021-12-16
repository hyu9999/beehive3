from pydantic import Field

from app.enums.user import 消息类型
from app.models.rwmodel import RWModel


class 消息配置(RWModel):
    title: str = Field(None, title="消息标题")
    content: str = Field(None, title="消息内容")
    redirect: str = Field(None, title="跳转地址")
    category: 消息类型 = Field(None, title="消息分类")
