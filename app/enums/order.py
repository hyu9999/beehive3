from enum import Enum, unique


@unique
class 订单状态(str, Enum):
    waiting = "0"  # 正在等待
    in_progress = "1"  # 处理中
    order_failed = "2"  # 下单失败
    part_finished = "3"  # 部分成交
    all_finished = "4"  # 全部成交
    failed = "5"  # 失败
    canceled = "6"  # 已取消


@unique
class EntrustOrderStatus(Enum):
    """委托订单状态"""
    SUBMITTING = "0"  # 提交中
    NO_DEAL = "1"     # 未成交
    WASTE = "2"       # 拒单
    PARTTRADED = "3"  # 部分成交
    DEAL = "4"        # 已成交
    WITHDRAWAL = "6"  # 已撤单


@unique
class OPFlagEnum(Enum):
    """委托订单类型"""
    COMMISSION = 1  # 委托
    DEAL_DONE = 2  # 已成交
    CANCELABLE = 3  # 可撤
