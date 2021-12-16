from datetime import datetime
from typing import List

from pydantic import Field

from app.enums.common import 回测评级数据集, 操作方向
from app.models import ROBOT_SID_RE
from app.models.base.robot import 机器人运行数据, 机器人配置, 装备配置, 机器人基本信息, 投资原则定义, 投资原则配置
from app.models.rwmodel import RWModel


class Robot(机器人运行数据, 机器人配置, 装备配置, 机器人基本信息):
    """机器人表"""

    投资原则: List[投资原则定义] = Field([], description="用户自定义")
    原则配置: List[投资原则配置] = Field(..., description="用户必填项，可配置参数值")


class 机器人回测指标(RWModel):
    标识符: str = Field(..., max_length=14, min_length=14, regex=ROBOT_SID_RE)
    交易日期: datetime
    Alpha: float
    Beta: float
    上涨概率: float
    交易天数: int
    交易次数: int
    信息比率: float
    入金: float
    出金: float
    基准年化收益率: float
    基准收益率: float
    基准波动率: float
    夏普比率: float
    平均仓位: float
    平均涨幅: float
    年化收益率: float
    收益: float
    收益波动率: float
    收益率: float
    最大单日涨幅: float
    最大单日跌幅: float
    最大回撤: float
    最大连续上涨天数: float
    最大连续下跌天数: float
    盈亏比: float
    盈利天数: float
    累计收益: float
    累计收益率: float
    累计交易成本: float
    股票仓位: float
    股票市值: float
    股票资产: float
    胜率: float
    资金余额: float
    资金周转率: float
    超额收益率: float
    近一周收益率: float
    近一月收益率: float
    交易成本: float
    平均交易成本: float
    平均交易次数: float
    平均盈亏比: float
    平均胜率: float
    近一周开始日期: datetime = None
    近一月开始日期: datetime = None
    近一年开始日期: datetime = None
    近一年收益率: float = None


class 机器人回测信号(RWModel):
    交易日期: datetime
    证券代码: str
    交易市场: str
    收盘价: float
    买卖方向: 操作方向
    个股持仓市值: float
    个股持仓数量: float
    个股卖出均价: float
    个股买入均价: float
    个股持仓变动: float
    个股收益率: float
    个股盈亏额: float
    个股资金变动: float
    个股持仓成本: float
    个股仓位占比: float
    行业分类: str
    证券名称: str
    标识符: str = Field(..., max_length=14, min_length=14, regex=ROBOT_SID_RE)


class 机器人回测评级(RWModel):
    年化收益率: float
    年化收益率得分: float = Field(None)
    评级: str
    最大回撤得分: float = Field(None)
    最大回撤平均得分: float = Field(None)
    年化收益率比最大回撤得分: float
    总得分: float
    夏普比率得分: float
    收益风险比得分: float
    收益风险比平均得分: float = Field(None)
    数据集: 回测评级数据集
    标识符: str = Field(..., max_length=14, min_length=14, regex=ROBOT_SID_RE)
    开始时间: datetime
    结束时间: datetime


class 机器人实盘信号(RWModel):
    交易日期: datetime
    证券代码: str
    交易市场: str
    收盘价: float
    买卖方向: 操作方向
    个股持仓市值: float
    个股持仓数量: float
    个股卖出均价: float
    个股买入均价: float
    个股持仓变动: float
    个股收益率: float
    个股盈亏额: float
    个股资金变动: float
    个股持仓成本: float
    个股仓位占比: float
    个股持仓天数: float
    个股累计交易成本: float
    个股交易成本: float
    行业分类: str
    证券名称: str
    标识符: str = Field(..., max_length=14, min_length=14, regex=ROBOT_SID_RE)


class 机器人实盘指标(RWModel):
    标识符: str = Field(..., max_length=14, min_length=14, regex=ROBOT_SID_RE)
    交易日期: datetime
    Alpha: float
    Beta: float
    上涨概率: float
    交易天数: int
    交易次数: int
    信息比率: float
    入金: float
    出金: float
    基准年化收益率: float
    基准收益率: float
    基准波动率: float
    夏普比率: float
    平均仓位: float
    平均涨幅: float
    年化收益率: float
    收益: float
    收益波动率: float
    收益率: float
    最大单日涨幅: float
    最大单日跌幅: float
    最大回撤: float
    最大连续上涨天数: float
    最大连续下跌天数: float
    盈亏比: float
    盈利天数: float
    累计收益: float
    累计收益率: float
    股票仓位: float
    股票市值: float
    股票资产: float
    胜率: float
    资金余额: float
    资金周转率: float
    超额收益率: float
    近一周收益率: float
    近一周最大回撤: float = None
    近一周交易胜率: float = None
    近一月收益率: float
    交易成本: float
    平均交易成本: float
    平均交易次数: float
    平均盈亏比: float
    平均胜率: float
    累计交易成本: float
    近一周开始日期: datetime = None
    近一月开始日期: datetime = None
    近一年开始日期: datetime = None
    近一年收益率: float = None



