from typing import Optional

from pydantic import Field

from app.enums.zvt_data import ZvtDataLogState
from app.models.base.zvt_data_log import ZvtDataLog
from app.models.rwmodel import RWModel


class ZvtDataLogInCreate(ZvtDataLog):
    ...


class ZvtDataLogInUpdate(ZvtDataLog):
    ...


class ZvtDataLogInPartialUpdate(RWModel):
    data_type: Optional[str] = Field(None, description="数据类型")
    name: Optional[str] = Field(None, description="名称")
    data_class: Optional[str] = Field(None, description="数据类")
    desc: Optional[str] = Field(None, description="解释")
    update_time: Optional[str] = Field(None, description="预计数据更新时间")
    state: Optional[ZvtDataLogState] = Field(None, description="状态")
