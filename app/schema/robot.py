from typing import List, Any, Optional

from pydantic import Field, AnyUrl

from app.enums.robot import 机器人可见模式, 默认原则配置, 机器人状态更新操作类型Enum
from app.models.base.profile import Profile
from app.models.robot import Robot, 投资原则配置, 机器人回测指标, 机器人回测评级, 机器人回测信号, 机器人实盘信号, 机器人实盘指标, 机器人运行数据, 装备配置
from app.models.rwmodel import RWModel
from app.schema.base import 分页Response

__uniform_field_name__ = {"标识符": "rid", "名称": "name", "简介": "description", "装备信息": "equipment_list"}


def uniform_alias(field_name: str):
    if field_name in __uniform_field_name__:
        return __uniform_field_name__[field_name]
    else:
        return field_name


class 机器人inResponse(Robot):
    作者: Profile


class 机器人附带分类(机器人inResponse):
    分类: str = "机器人"


class 机器人inCreate(装备配置):
    名称: str
    标识符: str = Field(None, max_length=14, min_length=14, regex=r"^(10|15)[\d]{6}[\w]{4}[\d]{2}$")
    头像: str = Field("5d47af9e50ea17146bb8c175", description="保存头像的id，通过此id可单独取出头像的内容")
    简介: str = Field(None, description="不少于10字不多于5000字的简单介绍", min_length=10, max_length=5000)
    主页地址: AnyUrl = None
    标签: List[str] = Field(..., max_items=8, max_length=10)
    可见模式: 机器人可见模式 = None
    原则配置: List[投资原则配置] = 默认原则配置
    下线原因: str = Field(None, min_length=1, max_length=100)


class 机器人BaseInUpdate(RWModel):
    名称: str = None
    头像: str = Field(None, description="保存头像的id，通过此id可单独取出头像的内容")
    简介: str = Field(None, description="不少于10字不多于5000字的简单介绍", min_length=10, max_length=5000)
    标签: List[str] = Field(None, max_items=8, max_length=10)
    主页地址: AnyUrl = None
    可见模式: 机器人可见模式 = None


class 机器人InUpdate(机器人BaseInUpdate):
    原则配置: List[投资原则配置] = None
    风控包列表: List[str] = Field(None, description="风控包标识符列表")
    择时装备列表: List[str] = Field(None, description="择时装备标识符列表")
    选股装备列表: List[str] = Field(None, description="选股装备标识符列表")
    交易装备列表: List[str] = Field(None, description="交易装备标识符列表")


class 机器人详情InResponse(机器人inResponse):
    风控包列表: List[Any] = Field(..., description="风控包标识符列表")
    择时装备列表: List[Any] = Field(..., description="择时装备标识符列表")
    风控装备列表: List[Any] = Field(..., description="风控装备标识符列表，其中风控包也作为一个风控装备填在内即可")
    选股装备列表: List[Any] = Field(..., description="选股装备标识符列表")
    交易装备列表: List[Any] = Field(..., description="交易装备标识符列表")


class 机器人运行数据InUpdate(机器人运行数据):
    pass


class 机器人回测详情InResponse(RWModel):
    机器人回测指标详情: 机器人回测指标
    机器人回测评级详情: 机器人回测评级
    机器人回测信号详情: List[机器人回测信号]


class 机器人商城列表InResponse(分页Response):
    数据: List[机器人inResponse]


class 机器人回测指标InCreate(机器人回测指标):
    pass


class 机器人回测信号InCreate(机器人回测信号):
    pass


class 机器人回测评级InCreate(机器人回测评级):
    pass


class 机器人实盘信号InCreate(机器人实盘信号):
    pass


class 机器人实盘指标InCreate(机器人实盘指标):
    pass


class 机器人推荐InResponse(RWModel):
    robot: Robot
    real_indicator: Optional[机器人实盘指标]
    reason: str = None


class 机器人推荐列表InResponse(分页Response):
    数据: List[机器人推荐InResponse]


class 智道机器人列表InResponse(分页Response):
    数据: List[机器人inResponse]


class RobotSetup(RWModel):
    可见模式: str
    name: str
    description: str


class 机器人状态InUpdate(RWModel):
    操作类型: 机器人状态更新操作类型Enum
    原因: Optional[str] = None
