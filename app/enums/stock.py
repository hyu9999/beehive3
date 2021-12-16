from enum import Enum, unique


@unique
class 股票市场Enum(str, Enum):
    上海 = "1"
    深圳 = "0"


@unique
class 自选股分类(str, Enum):
    portfolio = "portfolio"
    equipment = "equipment"
    robot = "robot"


@unique
class 自选股关联类型(str, Enum):
    subscribe = "subscribe"
    深圳 = "0"


@unique
class 出入金类型(str, Enum):
    出金 = "0"
    入金 = "1"
