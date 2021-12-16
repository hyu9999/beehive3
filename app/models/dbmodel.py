from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.rwmodel import PyObjectId


class DateTimeModelMixin(BaseModel):
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class DBModelMixin(DateTimeModelMixin):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")


class 数据字典(BaseModel):
    字段名称: str
    中文名称: str
    字段定义: str
    字段说明: str
