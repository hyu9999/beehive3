from enum import Enum, unique


@unique
class Exchange(str, Enum):
    """交易所."""

    CNSESH = "CNSESH"  # 上海证券交易所
    CNSESZ = "CNSESZ"  # 深圳证券交易所


@unique
class FlowTType(str, Enum):
    """流水类别."""

    DEPOSIT = "1"  # 入金
    WITHDRAW = "2"  # 出金
    BUY = "3"  # 买入
    SELL = "4"  # 卖出
    DIVIDEND = "5"  # 分红
    TAX = "6"  # 扣税


@unique
class CurrencyType(str, Enum):
    """货币类别."""

    CNY = "CNY"  # 人民币
    USD = "USD"  # 美元
    HKD = "HKD"  # 港币
