import re
from datetime import datetime
from typing import List, Any, Optional

from pydantic import Field, AnyUrl, validator

from app.enums.equipment import 装备分类_3, 装备信号传入方式, 装备可见模式, 择时分类, 装备状态, 装备状态更新操作类型Enum
from app.models import EQUIPMENT_SID_RE
from app.models.base.profile import Profile
from app.models.equipment import (
    Equipment,
    选股装备回测指标,
    选股装备回测信号,
    择时装备回测信号,
    择时装备回测指标,
    择时装备回测评级,
    择时装备实盘信号,
    择时装备实盘指标,
    选股装备实盘信号,
    选股装备实盘指标,
    装备运行数据,
    大类资产配置回测信号,
    大类资产配置回测指标,
    大类资产配置回测评级,
    大类资产配置实盘信号,
    大类资产配置实盘指标,
    基金定投实盘指标,
    基金定投实盘信号,
    基金定投回测评级,
    基金定投回测指标,
    基金定投回测信号,
)
from app.models.equipment import 选股装备回测评级
from app.models.rwmodel import RWModel
from app.schema.base import 分页Response


class 装备InCreate(RWModel):
    名称: str = None
    标识符: str = Field(None, regex=EQUIPMENT_SID_RE)
    简介: str = Field(None, description="不少于10字不多于5000字的简单介绍", min_length=10, max_length=5000)
    主页地址: AnyUrl = None
    分类: 装备分类_3 = None
    标签: List[str] = Field(..., max_items=8, max_length=10)
    英文名: str = None
    信号传入方式: 装备信号传入方式 = None
    可见模式: 装备可见模式 = None
    装备列表: List[str] = None
    指数列表: List[str] = None
    择时类型: 择时分类 = None
    源代码: str = None
    下线原因: str = Field(None, min_length=1, max_length=100)
    最佳调仓周期: int = Field(None, ge=3, le=60)

    @validator("最佳调仓周期")
    def validate_最佳调仓周期(cls, v, values):
        if values.get("信号传入方式") == 装备信号传入方式.手动传入 and v is None:
            raise ValueError("最佳调仓周期不能为空")

    @validator("分类")
    def validate_id(cls, v, values):
        if values.get("标识符"):
            if v == 装备分类_3.交易 and not re.fullmatch(r"^(01)[\d]{6}[\w]{4}[\d]{2}$", values["标识符"]):
                raise ValueError("交易装备标识符不符合规则")
            if v == 装备分类_3.选股 and not re.fullmatch(r"^(02)[\d]{6}[\w]{4}[\d]{2}$", values["标识符"]):
                raise ValueError("选股装备标识符不符合规则")
            if v == 装备分类_3.择时 and not re.fullmatch(r"^(03)[\d]{6}[\w]{4}[\d]{2}$", values["标识符"]):
                raise ValueError("择时装备标识符不符合规则")
            if v == 装备分类_3.风控 and not re.fullmatch(r"^(04)[\d]{6}[\w]{4}[\d]{2}$", values["标识符"]):
                raise ValueError("风控装备标识符不符合规则")
            if v == 装备分类_3.风控包 and not re.fullmatch(r"^(11)[\d]{6}[\w]{4}[\d]{2}$", values["标识符"]):
                raise ValueError("风控包标识符不符合规则")
        return v


class 装备BaseInUpdate(RWModel):
    名称: str = None
    主页地址: AnyUrl = None
    英文名: str = None
    简介: str = Field(None, description="不少于10字不多于5000字的简单介绍", min_length=10, max_length=5000)
    标签: List[str] = Field(None, max_items=8, max_length=10)
    装备列表: List[str] = None
    指数列表: List[str] = None
    可见模式: 装备可见模式 = None


class 装备InUpdate(装备BaseInUpdate):
    源代码: str = None


class 装备运行数据InUpdate(装备运行数据):
    pass


class 装备InResponse(Equipment):
    作者: Profile


class 新装备InCreate(RWModel):
    标识符: str = Field(..., regex=EQUIPMENT_SID_RE)
    名称: str
    版本: str
    一级分类: str
    二级分类: str
    作者: str
    创建时间: datetime
    上线时间: datetime = None
    装备列表: List[str] = None
    装备库版本: Optional[str] = Field("3.3")
    状态: 装备状态 = Field(装备状态.已上线)
    标签: List[str] = Field(None, max_items=8, max_length=10)
    简介: str = Field(None, description="不少于10字不多于5000字的简单介绍", min_length=10, max_length=5000)
    说明: str = Field(None, min_length=1, max_length=1000)
    详细说明: dict = Field(None)
    推荐搭配: List[str] = None
    资源信息: List[str] = None
    可连接装备类型: List[str] = None
    可选择触发器列表: List[str] = None
    配置参数: dict = None
    投资标的: str = None


class CandlestickInResponse(RWModel):
    时间戳: str = Field(None, description="时间戳")
    开盘价: float = Field(0, description="开盘价")
    最高价: float = Field(0, description="最高价")
    最低价: float = Field(0, description="最低价")
    收盘价: float = Field(0, description="收盘价")
    成交量: float = Field(0, description="成交量")


class 选股回测详情InResponse(RWModel):
    选股装备回测评级: 选股装备回测评级
    选股装备回测指标: 选股装备回测指标
    选股装备回测信号: 选股装备回测信号


class 装备商城列表InResponse(分页Response):
    数据: List[装备InResponse]


class 择时装备回测信号InCreate(择时装备回测信号):
    pass


class 择时装备回测指标InCreate(择时装备回测指标):
    pass


class 择时装备回测评级InCreate(择时装备回测评级):
    pass


class 择时装备实盘信号InCreate(择时装备实盘信号):
    pass


class 择时装备实盘指标InCreate(择时装备实盘指标):
    pass


class 选股装备回测信号InCreate(选股装备回测信号):
    pass


class 选股装备回测指标InCreate(选股装备回测指标):
    pass


class 选股装备回测评级InCreate(选股装备回测评级):
    pass


class 选股装备实盘信号InCreate(选股装备实盘信号):
    pass


class 选股装备实盘指标InCreate(选股装备实盘指标):
    pass


class 大类资产配置回测信号InCreate(大类资产配置回测信号):
    pass


class 大类资产配置回测指标InCreate(大类资产配置回测指标):
    pass


class 大类资产配置回测评级InCreate(大类资产配置回测评级):
    pass


class 大类资产配置实盘信号InCreate(大类资产配置实盘信号):
    pass


class 大类资产配置实盘指标InCreate(大类资产配置实盘指标):
    pass


class 基金定投回测信号InCreate(基金定投回测信号):
    pass


class 基金定投回测指标InCreate(基金定投回测指标):
    pass


class 基金定投回测评级InCreate(基金定投回测评级):
    pass


class 基金定投实盘信号InCreate(基金定投实盘信号):
    pass


class 基金定投实盘指标InCreate(基金定投实盘指标):
    pass


class 装备列表InResponse(分页Response):
    数据: List[装备InResponse]


class GradeStrategyWords(RWModel):
    """风险等级与对应的风险话术"""

    grade: str = Field(None, description="风险等级")
    strategy_words: str = Field(None, description="风险话术")


class SymbolGradeStrategyWordsInresponse(RWModel):
    """某股票对应的风险等级与风险话术列表"""

    symbol: str = Field(..., description="股票代码")
    grade_strategy_word: List[GradeStrategyWords] = Field([], description="风险等级与风险话术列表")


class EquipmentExecute(RWModel):
    """装备运行入参"""

    input_values: dict = Field({}, description="装备入参")
    run_config: dict = Field({}, description="装备配置")
    category: str = Field("ETF", description="分类")
    industry_list: List[str] = Field([], description="行业列表")


class 装备状态InUpdate(RWModel):
    操作类型: 装备状态更新操作类型Enum
    原因: Optional[str] = None
