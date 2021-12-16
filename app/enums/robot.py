from enum import Enum, unique

from stralib.robot.buy_strategy import buy_signal_identical, buy_signal_num, buy_screen_stock, atr_sure_stock_list, pe_sure_stock_list
from stralib.robot.sold_strategy import achieve_max_hold_days, achieve_stopdown, achieve_stopup, trade_sell_signal, risk_signal


@unique
class 机器人状态(str, Enum):
    创建中 = "创建中"
    审核中 = "审核中"
    审核未通过 = "审核未通过"
    已上线 = "已上线"
    已下线 = "已下线"
    已删除 = "已删除"
    临时回测 = "临时回测"


@unique
class 机器人评级(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    N = "N"


@unique
class 机器人可见模式(str, Enum):
    完全公开 = "完全公开"
    不公开 = "不公开"
    仅对我的客户公开 = "仅对我的客户公开"


@unique
class 可配置原则(str, Enum):
    最大调仓周期 = "最大调仓周期"
    最大持仓数量 = "最大持仓数量"
    止盈点 = "止盈点"
    止损点 = "止损点"
    交易费率 = "交易费率"


@unique
class 机器人分类(str, Enum):
    趋势投资型 = "趋势投资型"
    价值投资型 = "价值投资型"
    成长投资型 = "成长投资型"
    量化投资型 = "量化投资型"
    被动投资型 = "被动投资型"
    综合型 = "综合型"


class 减仓模式(str, Enum):
    同比例减仓 = "tb_reduce_position"
    去弱留强 = "qrlq_reduce_position"


class 卖出筛选器(str, Enum):
    超过最大持仓周期 = achieve_max_hold_days
    超过止损点 = achieve_stopdown
    超过止盈点 = achieve_stopup
    交易卖出信号 = trade_sell_signal
    风控信号 = risk_signal


class 买入筛选器(str, Enum):
    买交易选股都有信号的股 = buy_signal_identical
    买推荐次数最多的股 = buy_signal_num
    买选股信号的股 = buy_screen_stock


class 保证持仓数量筛选器(str, Enum):
    ATR技术指标筛选 = atr_sure_stock_list
    PE筛选 = pe_sure_stock_list


class 运行方式(str, Enum):
    service = "service"  # beehive中使用
    backtest = "backtest"  # 回测中使用


默认原则配置 = [
    {"唯一名称": "max_hold_day", "中文名称": "最大调仓周期", "配置规则": "默认值或用户自定义", "配置值": "60"},
    {"唯一名称": "max_hold_num", "中文名称": "最大持仓数量", "配置规则": "默认值或用户自定义", "配置值": "5"},
    {"唯一名称": "stopup", "中文名称": "止盈点", "配置规则": "默认值或用户自定义", "配置值": "15"},
    {"唯一名称": "stopdown", "中文名称": "止损点", "配置规则": "默认值或用户自定义", "配置值": "8"},
    {"唯一名称": "tax_rate", "中文名称": "交易费率", "配置规则": "默认值或用户自定义", "配置值": "0.0016"},
]


class 错误类型Enum(str, Enum):
    error = "错误"
    warning = "提醒"


@unique
class 机器人状态更新操作类型Enum(str, Enum):
    上线 = "上线"
    下线 = "下线"
    删除 = "删除"
