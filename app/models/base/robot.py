from datetime import datetime
from typing import List, Optional

from pydantic import Field
from stralib.models.robot import 减仓模式分类, 卖出筛选器分类, 买入筛选器分类, 保证持仓数量筛选器分类

from app.enums.robot import 机器人状态, 可配置原则, 机器人评级, 机器人可见模式
from app.models.rwmodel import RWModel


class 机器人基本信息(RWModel):
    标识符: str = Field(..., max_length=14, min_length=14, regex=r"^(10|15)[\d]{6}[\w]{4}[\d]{2}$")
    名称: str
    头像: str = Field("5d47af9e50ea17146bb8c175", description="保存头像的id，通过此id可单独取出头像的内容")
    简介: str = Field(None, description="不少于10字不多于5000字的简单介绍", min_length=10, max_length=5000)
    作者: str = Field(...)
    状态: 机器人状态
    创建时间: datetime = None
    上线时间: datetime = None
    下线时间: datetime = None
    标签: List[str]
    可见模式: 机器人可见模式 = None
    评级: 机器人评级 = Field(None)
    下线原因: str = Field(None, min_length=1, max_length=100)
    文章标识符: int = Field(None, description="社区文章id")
    版本: str = Field(None)
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class 装备配置(RWModel):
    风控包列表: List[str] = Field(..., description="风控包标识符列表")
    择时装备列表: List[str] = Field([], max_items=1, min_items=0, description="择时装备标识符列表")
    风控装备列表: List[str] = Field([], description="风控装备标识符列表，其中风控包也作为一个风控装备填在内即可")
    选股装备列表: List[str] = Field([], max_items=3, min_items=0, description="选股装备标识符列表")
    交易装备列表: List[str] = Field([], max_items=3, min_items=0, description="交易装备标识符列表")


class 机器人自身运行数据(RWModel):
    分析了多少支股票: int = Field(0)
    运行天数: int = Field(0)
    累计产生信号数: int = Field(0)
    计算时间: Optional[datetime]
    订阅人数: int = int(0)
    累计收益率: float = Field(0)


class 组合相关运行数据(RWModel):
    管理了多少组合: int = Field(0)
    累计服务人数: int = Field(0)
    累计管理资金: float = Field(0)
    累计创造收益: float = Field(0)


class 机器人运行数据(机器人自身运行数据, 组合相关运行数据):
    ...


class 机器人配置(RWModel):
    减仓模式: List[减仓模式分类] = Field([减仓模式分类.tb_reduce_position], description="减仓模式")
    卖出筛选器: List[卖出筛选器分类] = Field(
        [卖出筛选器分类.achieve_stopdown, 卖出筛选器分类.achieve_max_hold_days, 卖出筛选器分类.achieve_stopup, 卖出筛选器分类.trade_sell_signal, 卖出筛选器分类.risk_signal], description="卖出筛选器"
    )
    买入筛选器: List[买入筛选器分类] = Field([买入筛选器分类.buy_signal_identical], description="买入筛选器")
    保证持仓数量筛选器: List[保证持仓数量筛选器分类] = Field([保证持仓数量筛选器分类.atr_sure_stock_list], description="再次过滤选出来的股票保证用户持仓小于等于持仓数量")


class 投资原则定义(RWModel):
    原则名称: str = Field(..., description="原则名称")
    原则内容: str = Field(..., description="原则内容")


class 投资原则配置(RWModel):
    唯一名称: str = Field(..., description="和投资原则定义中一致")
    中文名称: 可配置原则
    配置规则: str = Field(..., description="用正则表达式设定配置值的检查")
    配置值: str = Field(..., description="配置值")
