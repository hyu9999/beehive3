from typing import List, Dict

from pydantic import Field

from app.models.rwmodel import RWModel


class 权限基本信息(RWModel):
    role: str = Field(None, title="角色")
    permissions: Dict[str, List[str]] = Field({}, title="权限")
