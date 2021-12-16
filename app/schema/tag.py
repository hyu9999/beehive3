from pydantic import BaseModel, Field

from app.enums.tag import TagType


class TagInUpdate(BaseModel):
    name: str = Field(None, title="名称")
    category: TagType = Field(None, title="分类")
