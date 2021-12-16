from pydantic import Field

from app.models.rwmodel import RWModel


class 角色基本信息(RWModel):
    name: str = Field(..., title="角色名称")
