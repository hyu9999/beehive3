from typing import List, Optional
from datetime import datetime

from pydantic import Field

from app.enums.publish import 策略分类enum, 发布情况enum, 错误信息数据类型enum, 错误信息错误类型enum, 错误触发源enum
from app.models.rwmodel import RWModel


class StrategyErrorLogDetail(RWModel):
    """错误信息."""
    触发源: 错误触发源enum
    数据类型: 错误信息数据类型enum
    错误类型: 错误信息错误类型enum
    详情: str
    写入时间: datetime = Field(default_factory=datetime.utcnow)


class StrategyDailyLog(RWModel):
    """策略每日日志."""
    分类: 策略分类enum
    标识符: str
    交易日期: datetime
    发布情况: 发布情况enum
    写入时间: datetime = Field(default_factory=datetime.utcnow)
    错误信息: List[StrategyErrorLogDetail]


class StrategyPublishLog(RWModel):
    """策略发布日志."""
    username: str = Field(..., description="厂商用户名")
    交易日期: datetime
    总共发布策略数量: int
    当日发布策略数量: int
    报错策略数量: int
    成功策略数量: int
    已上线策略数量: int
    已下线策略数量: int
    是否完成发布: bool
    错误策略: Optional[List[str]]
