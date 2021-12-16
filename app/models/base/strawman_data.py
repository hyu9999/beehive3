from datetime import datetime, date
from enum import Enum
from typing import List, Dict, Generic, TypeVar, Optional

from pydantic import Field
from pydantic.generics import GenericModel

from app.enums.log import 买卖方向
from app.enums.security import 证券交易所
from app.models.rwmodel import RWModel

DataT = TypeVar("DataT")


class TimeSeriesResponseTemplate(GenericModel, Generic[DataT]):
    """ 模板类：可以是某个类的list或者一个以日期为key，某个类为value的字典 """

    dict_data: Optional[Dict[date, List[DataT]]]
    list_data: Optional[List[DataT]]
    交易日期: datetime = None


class 指标数据(RWModel):
    指标日期: datetime
    交易所: 证券交易所
    股票代码: str
    指标数值: float


class 信号基础类(RWModel):
    TDATE: date = Field(..., alias="信号日期")
    SYMBOL: str = Field(..., alias="股票代码")
    EXCHANGE: 证券交易所 = Field(..., alias="交易所")
    TCLOSE: float = Field(..., alias="收盘价")
    话术编号: int = Field(None)
    OPERATOR: int = Field(None, alias="操作符编号")


class 选股装备信号(RWModel):
    TDATE: date = Field(..., alias="信号日期")
    SYMBOL: str = Field(..., alias="股票代码", description="空值表示当天没有信号")
    EXCHANGE: 证券交易所 = Field(..., alias="交易所", description="空值表示当天没有信号")
    TCLOSE: float = Field(0, alias="收盘价")
    SCORE: float = Field(0, alias="得分", description="如果当日无信号，则得分为0")


class 交易装备信号(信号基础类):
    买卖方向: 买卖方向
    指标数值: float


class 市场趋势形态(str, Enum):
    下降 = "下降"
    反弹 = "反弹"
    回落 = "回落"
    上升 = "上升"
    严重低估 = "严重低估"
    估值低估 = "估值低估"
    估值正常 = "估值正常"
    估值高估 = "估值高估"
    严重高估 = "严重高估"


class 择时装备信号(RWModel):
    信号日期: date
    市场趋势形态: 市场趋势形态
    建议仓位: str
    理想仓位: float
    估值分位数: Optional[float]


class 风控装备信号(RWModel):
    tdate: date = Field(..., alias="信号日期", description="空值表示当天没有信号")
    symbol: str = Field(..., alias="股票代码", description="空值表示当天没有信号")
    exchange: 证券交易所 = Field(..., alias="交易所", description="空值表示当天没有信号")
    中文名称: str


class 价格建议(Enum):
    T日收盘价 = 0
    T1日开盘价 = -1


class 选股回测数据(RWModel):
    回测交易日: date
    回测资金: float
    调仓周期: int
    每日盈亏: float
    策略收益率: float
    策略年化收益率: float
    基准收益率: float
    Alpha: float
    Beta: float
    夏普比率: float
    最大回撤: float
    基准波动率: float
    策略波动率: float
    信息比率: float
    最大单日涨幅: float
    最大单日跌幅: float
    剧烈上涨环境胜率: float
    平缓上涨环境胜率: float
    宽幅震荡环境胜率: float
    窄幅震荡环境胜率: float
    平缓下跌环境胜率: float
    剧烈下跌环境胜率: float


class 择时回测数据(RWModel):
    回测交易日: date
    回测资金: float
    准确率: float
    策略收益率: float
    策略正确率: float
    指数收益率: float
    策略超额收益率: float


class 选股评级数据(RWModel):
    统计年份: str
    年度最大回撤: float
    年度最大回撤得分: float
    年度评级: str


class 择时评级数据(RWModel):
    统计年份: str
    年度交易天数: int
    年度准确率: float
    年度评级: str


class 装备信号数量(RWModel):
    标识符: str
    开始时间: date
    结束时间: date
    信号数量: int


class 装备信号中某股票数量(RWModel):
    标识符: str
    证券代码: str
    开始时间: date
    结束时间: date
    出现次数: int
