from datetime import datetime
from typing import Optional

from pydantic import Field

from app.enums.common import 回测评级数据集, 操作方向
from app.enums.equipment import 市场风格
from app.models import TIMING_SID_RE, SCREEN_SID_RE, 大类资产配置_SID_RE, 基金定投_SID_RE, ROBOT_SID_RE
from app.models.rwmodel import RWModel


########################################################################################################################################
# 择时装备
########################################################################################################################################
class 择时装备(RWModel):
    标识符: str = Field(..., regex=TIMING_SID_RE)


class 择时信号基本信息(择时装备):
    交易日期: datetime
    账户资产: float
    收益率: float
    累计收益率: float
    标的指数: str


class 择时回测信号基本信息(择时信号基本信息):
    ...


class 择时实盘信号基本信息(择时信号基本信息):
    近一周收益率: float
    近一月收益率: float


class 择时指标基本信息(择时装备):
    开始时间: datetime
    结束时间: datetime
    交易总天数: int
    获胜天数: int
    胜率: float
    收益率: float
    超额收益率: float
    标的指数: str
    标的指数收益率: float


class 择时回测指标基本信息(择时指标基本信息):
    """估值类择时：获胜天数/胜率字段可为空，为方便数据输入输出，目前默认为0"""

    回测年份: str


class 择时实盘指标基本信息(择时指标基本信息):
    实盘年份: str


class 择时回测评级基本信息(择时装备):
    开始时间: datetime
    结束时间: datetime
    回测年份: str
    收益率得分: float
    胜率得分: float
    胜率和收益率得分: float
    最大回撤得分: float
    收益风险比得分: float
    评级: str
    总得分: float
    标的指数: str


########################################################################################################################################
# 选股装备
########################################################################################################################################
class 选股装备(RWModel):
    标识符: str = Field(..., regex=SCREEN_SID_RE)


class 选股信号基本信息(选股装备):
    交易日期: datetime
    账户资产: float
    收益率: float
    累计收益率: float
    近一周收益率: float
    近一月收益率: float


class 选股回测信号基本信息(选股信号基本信息):
    ...


class 选股实盘信号基本信息(选股信号基本信息):
    ...


class 选股指标基本信息(选股装备):
    开始时间: datetime
    结束时间: datetime
    最佳调仓周期: int
    收益率: float
    累计收益率: Optional[float]
    年化收益率: float
    基准收益率: float
    Alpha: float
    Beta: float
    夏普比率: float
    最大回撤: float
    波动率: float
    信息比率: float
    最大单日涨幅: float
    最大单日跌幅: float
    剧烈上涨环境胜率: float
    平缓上涨环境胜率: float
    宽幅震荡环境胜率: float
    窄幅震荡环境胜率: float
    平缓下跌环境胜率: float
    剧烈下跌环境胜率: float
    数据集: Optional[回测评级数据集]


class 选股回测指标基本信息(选股指标基本信息):
    胜率: float
    适用市场: 市场风格
    平均每日选股数: int
    总交易日数量: int
    总信号数量: int


class 选股实盘指标基本信息(选股指标基本信息):
    持股时间: int
    盈利次数: int
    盈利次数占比: float
    盈亏率: float
    基准年化收益率: float
    平均选股数量: float
    最大选股数量: int
    策略超额收益率: float
    最近一年的盈利次数占比: float
    最近一年的收益率: float


class 选股回测评级基本信息(选股装备):
    开始时间: datetime
    结束时间: datetime
    数据集: 回测评级数据集
    胜率得分: float
    评级: str
    总得分: float
    年化收益率得分: float = Field(None)
    最大回撤得分: float = Field(None)
    夏普比率得分: float = Field(None)
    胜率总得分: float = Field(None)
    调仓周期: int


########################################################################################################################################
# 大类资产配置
########################################################################################################################################
class 大类资产配置(RWModel):
    标识符: str = Field(..., regex=大类资产配置_SID_RE)


class 大类资产配置信号基本信息(RWModel):
    交易日期: datetime
    个股买入均价: float
    个股交易成本: float
    个股仓位占比: float
    个股卖出均价: float
    个股持仓变动: float
    个股持仓天数: float
    个股持仓市值: float
    个股持仓成本: float
    个股持仓数量: float
    个股收益率: float
    个股盈亏额: float
    个股累计交易成本: float
    个股资金变动: float
    买卖方向: 操作方向
    交易市场: str
    收盘价: float
    证券代码: str
    证券名称: str


class 大类资产配置回测信号基本信息(大类资产配置, 大类资产配置信号基本信息):
    ...


class 大类资产配置实盘信号基本信息(大类资产配置, 大类资产配置信号基本信息):
    ...


class 大类资产配置指标基本信息(大类资产配置):
    交易日期: datetime
    Alpha: float
    Beta: float
    上涨概率: float
    交易天数: int
    交易成本: float
    交易次数: int
    信息比率: float
    入金: float
    出金: float
    基准年化收益率: float
    基准收益率: float
    基准波动率: float
    夏普比率: float
    平均交易成本: float
    平均交易次数: float
    平均仓位: float
    平均涨幅: float
    平均盈亏比: float
    平均胜率: float
    年化收益率: float
    收益: float
    收益波动率: float
    收益率: float
    最大单日涨幅: float
    最大单日跌幅: float
    最大回撤: float
    最大连续上涨天数: int
    最大连续下跌天数: int
    盈亏比: float
    盈利天数: int
    累计交易成本: float
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
    近一月收益率: float
    近一年收益率: float
    近一周开始日期: datetime
    近一月开始日期: datetime
    近一年开始日期: datetime


class 大类资产配置回测指标基本信息(大类资产配置指标基本信息):
    ...


class 大类资产配置实盘指标基本信息(大类资产配置指标基本信息):
    ...


class 大类资产配置回测评级基本信息(大类资产配置):
    开始时间: datetime
    结束时间: datetime
    数据集: 回测评级数据集
    评级: str
    总得分: float
    年化收益率: float
    年化收益率得分: float
    年化收益率比最大回撤得分: float
    收益风险比平均得分: float
    收益风险比得分: float
    最大回撤得分: float
    最大回撤平均得分: float
    夏普比率得分: float


########################################################################################################################################
# 基金定投
########################################################################################################################################
class 基金定投(RWModel):
    标识符: str = Field(..., regex=基金定投_SID_RE)


class 基金定投回测信号基本信息(基金定投, 大类资产配置信号基本信息):
    ...


class 基金定投实盘信号基本信息(基金定投, 大类资产配置信号基本信息):
    ...


class 基金定投回测指标基本信息(基金定投, 大类资产配置指标基本信息):
    ...


class 基金定投实盘指标基本信息(基金定投, 大类资产配置指标基本信息):
    ...


class 基金定投回测评级基本信息(基金定投, 大类资产配置回测评级基本信息):
    ...


########################################################################################################################################
# 机器人
########################################################################################################################################
class 机器人(RWModel):
    标识符: str = Field(..., regex=ROBOT_SID_RE)


class 机器人指标(机器人):
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


class 机器人回测指标基本信息(机器人指标):
    ...


class 机器人实盘指标基本信息(机器人指标):
    近一周最大回撤: float = None
    近一周交易胜率: float = None


class 机器人信号(机器人):
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


class 机器人回测信号基本信息(机器人信号):
    ...


class 机器人实盘信号基本信息(机器人信号):
    个股持仓天数: float
    个股累计交易成本: float
    个股交易成本: float


class 机器人回测评级基本信息(机器人):
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
    开始时间: datetime
    结束时间: datetime
