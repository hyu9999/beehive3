from datetime import datetime
from typing import List

from pydantic import Field

from app.enums.fund_account import CurrencyType
from app.models.base.stock import 股票基本信息
from app.models.rwmodel import RWModel, PyObjectId
from app.enums.portfolio import 组合状态, 投资类型, 风险点状态, 风险类型


class 用户资金账户信息(RWModel):
    userid: str = Field(None, title="用户id", description="券商系统或者模拟交易系统分配的用户名。有些系统会分配两个账号，都需要提供才可以对应资金账号，如蘑菇的接口。")
    fundid: str = Field(None, title="资金账户id", description="券商系统或者模拟交易系统分配的资金账号的id")
    currency: CurrencyType = Field(CurrencyType.CNY, description="货币")
    create_date: datetime = Field(None, title="创建日期")


class 组合配置(RWModel):
    max_period: int = Field(10951, title="投资周期")
    expected_return: float = Field(0.2, title="预期收益率")


class 组合机器人配置(RWModel):
    adjust_cycle: int = Field(100, title="调仓周期")
    max_quantity: int = Field(10, title="最大持股数")
    open_risks: List[str] = Field([], title="个股风险配置")


class 风险点信息(RWModel):
    # ToDo date风险发现时间字段需重命名，防止与date时间模块冲突
    id: PyObjectId = Field(..., title="风险点id")
    name: str = Field(None, title="名称")
    status: 风险点状态 = Field(..., title="风险点状态")
    risk_type: 风险类型 = Field(..., title="风险类型")
    symbol_name: str = Field(None, title="股票名称")
    symbol: str = Field(None, title="股票代码")
    exchange: str = Field(None, title="交易所")
    date: datetime = Field(None, title="风险发现时间")
    price: float = Field(None, title="止盈或者止损价格")
    ratio: float = Field(None, title="净有息负债率")
    opinion: str = Field(None, title="审计意见类型")
    position_rate: float = Field(None, title="仓位")
    position_advice: List[float] = Field([], title="推荐仓位")
    data: List = Field([], title="展示数据")


class 交易统计信息(RWModel):
    trade_frequency: int = Field(None, title="交易次数")
    winning_rate: float = Field(None, title="交易胜率")
    profit_loss_ratio: float = Field(None, title="交易盈亏比")
    trade_cost: float = Field(None, title="交易成本")


class 个股统计信息(股票基本信息):
    cost_price: float = Field(None, title="成本价")
    profit: float = Field(None, title="收益")
    profit_rate: float = Field(None, title="收益率")
    trade_frequency: int = Field(None, title="交易次数")


class 统计数据详情信息(RWModel):
    trade_stats: 交易统计信息 = Field({}, title="交易统计数据")
    stock_stats: List[个股统计信息] = Field([], title="个股统计数据")


class 统计数据信息(RWModel):
    portfolio: PyObjectId = Field(..., title="组合")
    last_tdate: 统计数据详情信息 = Field(统计数据详情信息(), title="昨天")
    last_week: 统计数据详情信息 = Field(统计数据详情信息(), title="近一周")
    last_month: 统计数据详情信息 = Field(统计数据详情信息(), title="近一月")
    last_3_month: 统计数据详情信息 = Field(统计数据详情信息(), title="近三月")
    last_half_year: 统计数据详情信息 = Field(统计数据详情信息(), title="近半年")
    last_year: 统计数据详情信息 = Field(统计数据详情信息(), title="近一年")


class 总收益排行信息(RWModel):
    profit_rate: float = Field(0, title="总收益")
    rank: int = Field(None, title="排行")
    over_percent: float = Field(0, title="超过人数比例")


class 组合基本信息(RWModel):
    name: str = Field("默认组合", title="名称")
    status: 组合状态 = Field("running", title="组合状态")
    username: str = Field(..., title="用户")
    fund_account: List[用户资金账户信息] = Field(..., title="用户资金账户")
    initial_funding: float = Field(..., title="初始资金")
    invest_type: 投资类型 = Field("stock", title="投资类型")
    tags: List[str] = Field([], title="标签")
    introduction: str = Field("", title="组合介绍")
    config: 组合配置 = Field(组合配置(), title="组合目标")
    robot_config: 组合机器人配置 = Field(组合机器人配置(), title="机器人原则")
    risks: List[风险点信息] = Field([], title="风险点")
    is_open: bool = Field(True, title="是否开放")
    robot: str = Field(..., title="机器人")
    subscribe_num: int = Field(0, title="订阅数量")
    subscribers: List[str] = Field([], title="订阅者")
    article_id: int = Field(None, title="社区文章id")


class 组合阶段收益(RWModel):
    total: float = Field(0, title="总收益率")
    last_tdate: float = Field(0, title="日收益率")
    last_week: float = Field(0, title="周收益率")
    last_month: float = Field(0, title="月收益率")
    last_3_month: float = Field(0, title="季度收益率")
    last_half_year: float = Field(0, title="半年收益率")
    last_year: float = Field(0, title="年收益率")
