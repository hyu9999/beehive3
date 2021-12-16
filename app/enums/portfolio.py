from enum import Enum, unique


@unique
class 组合状态(str, Enum):
    running = "running"  # 正在进行中
    closed = "closed"  # 已经结束


@unique
class 投资类型(str, Enum):
    stock = "stock"  # 股票
    fund = "fund"  # 基金


@unique
class 风险点状态(str, Enum):
    confirm = "00"  # 待确认
    confirmed = "11"  # 已确认
    ignored = "12"  # 已忽略
    solving = "20"  # 解决中
    resolved = "30"  # 已解决
    unresolved = "31"  # 未解决


@unique
class 风险类型(str, Enum):
    stop_profit = "0"  # 股票到达了止盈点
    stop_loss = "1"  # 股票到达了止损点
    audit_opinion = "2"  # 审计意见风险
    short_term_trend_break = "3"  # 短期走势破位
    net_interest_bearing_debt_ratio = "4"  # 净有息负债率
    is_st = "5"  # 该股票已经被 ST
    potential_st = "6"  # 该股票有潜在 ST 风险
    bear_market = "7"  # 空头行情
    overweight = "8"  # 仓位过重
    underweight = "9"  # 仓位过轻
    adjustment_cycle = "10"  # 达到调仓周期
    sell_signal = "12"  # 交易策略给出的卖出信号
    clearance_line = "13"  # 到达用户设置的清仓线


@unique
class 数据同步方式(str, Enum):
    auto = "auto"  # 自动
    manual = "manual"  # 手动


@unique
class PortfolioCategory(str, Enum):
    """组合种类"""

    ManualImport = "ManualImport"  # 手动导入
    SimulatedTrading = "SimulatedTrading"  # 模拟交易


@unique
class ReturnYieldCalculationMethod(str, Enum):
    """收益率计算方式."""

    SWR = "简单收益率"
    TWR = "时间加权收益率"
    MWR = "现金加权收益率"
