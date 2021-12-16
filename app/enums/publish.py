from enum import Enum, unique


@unique
class 策略分类enum(str, Enum):
    机器人 = "机器人"
    选股 = "选股"
    择时 = "择时"
    交易 = "交易"
    风控 = "风控"
    基金定投 = "基金定投"
    大类资产配置 = "大类资产配置"


@unique
class 发布情况enum(str, Enum):
    unpublished = "未发布"
    success = "发布成功"
    failed = "发布失败"


@unique
class 错误触发源enum(str, Enum):
    回测 = "回测"
    实盘 = "实盘"


@unique
class 错误信息数据类型enum(str, Enum):
    评级 = "评级"
    信号 = "信号"
    指标 = "指标"


@unique
class 错误信息错误类型enum(str, Enum):
    数据格式 = "数据格式"
    日期连续性 = "日期连续性"
    数据完整性 = "数据完整性"
    缺失策略 = "缺失策略"
    重复写入数据 = "重复写入数据"


@unique
class 策略状态enum(str, Enum):
    已上线 = "已上线"
    已下线 = "已下线"
