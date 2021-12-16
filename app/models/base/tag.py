from pydantic import Field

from app.enums.tag import TagType
from app.models.rwmodel import RWModel


class 标签基本信息(RWModel):
    name: str = Field(..., title="名称")
    category: TagType = Field(..., title="分类")
