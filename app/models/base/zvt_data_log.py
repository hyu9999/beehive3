from typing import Optional
from datetime import datetime

from pydantic import Field

from app.enums.zvt_data import ZvtDataLogState
from app.models.rwmodel import RWModel


class ZvtDataLogType(RWModel):
    """ZVT数据日志数据类型"""
    name: str = Field(..., description="名称")


class ZvtDataLog(RWModel):
    """Zvt数据日志."""
    data_type: str = Field(..., description="数据类型")
    name: str = Field(..., description="名称")
    data_class: str = Field(..., description="数据类")
    desc: str = Field(..., description="解释")
    update_time: str = Field(..., description="预计数据更新时间")
    updated_at: Optional[datetime] = Field(None, description="实际数据更新时间")
    state: ZvtDataLogState = Field(..., description="状态")
