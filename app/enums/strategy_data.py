from enum import unique, Enum


@unique
class 策略名称(str, Enum):
    机器人 = "机器人"
    选股装备 = "选股"
    择时装备 = "择时"
    大类资产配置 = "大类资产配置"
    基金定投 = "基金定投"


@unique
class 策略数据类型(str, Enum):
    回测信号 = "回测信号"
    回测指标 = "回测指标"
    回测评级 = "回测评级"
    实盘信号 = "实盘信号"
    实盘指标 = "实盘指标"


@unique
class 策略名称_EN(str, Enum):
    机器人 = "robot"
    选股 = "screen"
    择时 = "timing"
    交易 = "trade"
    风控 = "riskman"
    风控包 = "package"
    大类资产配置 = "asset_allocation"
    基金定投 = "aipman"
