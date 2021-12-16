from typing import Any, List

from pydantic.fields import Field

from app.models.rwmodel import RWModel


class 分页Response(RWModel):
    数据: List[Any] = Field([], description="数据列表")
    总数据量: int = Field(0, description="统计数据列表条数")
    总页数: int = Field(0, description="统计总的分页数")


class UpdateResult(RWModel):
    matched_count: int = Field(..., description="匹配数")
    modified_count: int = Field(..., description="更新数")
