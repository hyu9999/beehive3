from enum import unique, Enum


@unique
class 策略分类(str, Enum):
    交易 = "01"
    选股 = "02"
    择时 = "03"
    风控 = "04"
    仓位分配 = "05"
    大类资产配置 = "06"
    基金定投 = "07"
    风控包 = "11"
    机器人 = "10"
