from enum import Enum, unique


@unique
class 买卖方向(str, Enum):
    buy = "buy"
    sell = "sell"
    unchanged = "unchanged"


@unique
class 日志分类(str, Enum):
    portfolio = "portfolio"
    robot = "robot"
    equipment = "equipment"
