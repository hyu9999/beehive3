from enum import Enum, unique


@unique
class 装备状态(str, Enum):
    创建中 = "创建中"
    未审核 = "未审核"
    审核中 = "审核中"
    审核未通过 = "审核未通过"
    已上线 = "已上线"
    已下线 = "已下线"
    已删除 = "已删除"


@unique
class 装备分类_3(str, Enum):
    """
    其中机器人是组合和套餐的别名。包是一组同类型的装备的集合。
    """
    交易 = "交易"
    选股 = "选股"
    择时 = "择时"
    风控 = "风控"
    仓位分配 = "仓位分配"
    大类资产配置 = "大类资产配置"
    基金定投 = "基金定投"
    风控包 = "风控包"


@unique
class 装备分类转换(str, Enum):
    """
            | 装备类型     | 编号 |
            | ------------ | ---- |
            | 交易         | 01   |
            | 选股         | 02   |
            | 择时         | 03   |
            | 风控         | 04   |
            | 仓位分配     | 05   |
            | 大类资产配置 | 06   |
            | 基金定投     | 07   |
            | 机器人         | 10   |
            | 包          | 11   |
    """

    交易 = "01"
    选股 = "02"
    择时 = "03"
    风控 = "04"
    仓位分配 = "05"
    大类资产配置 = "06"
    基金定投 = "07"
    风控包 = "11"


@unique
class 装备评级(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    N = "N"  # 源代码运行异常


@unique
class 装备信号传入方式(str, Enum):
    """信号传入方式"""

    手动传入 = "手动传入"
    接口传入 = "接口传入"
    源代码传入 = "源代码传入"


@unique
class 装备可见模式(str, Enum):
    完全公开 = "完全公开"
    不公开 = "不公开"
    仅对我的客户公开 = "仅对我的客户公开"


@unique
class 择时分类(str, Enum):
    趋势类 = "趋势类"
    估值类 = "估值类"


@unique
class 选股CollectionName(str, Enum):
    backtest_signal = "选股回测信号collection名"
    backtest_indicator = "选股回测指标collection名"
    backtest_assess = "选股回测评级collection名"
    real_signal = "选股实盘信号collection名"
    real_indicator = "选股实盘指标collection名"


@unique
class 择时CollectionName(str, Enum):
    backtest_signal = "择时回测信号collection名"
    backtest_indicator = "择时回测指标collection名"
    backtest_assess = "择时回测评级collection名"
    real_signal = "择时实盘信号collection名"
    real_indicator = "择时实盘指标collection名"


@unique
class 大类资产配置CollectionName(str, Enum):
    backtest_signal = "大类资产配置回测信号collection名"
    backtest_indicator = "大类资产配置回测指标collection名"
    backtest_assess = "大类资产配置回测评级collection名"
    real_signal = "大类资产配置实盘信号collection名"
    real_indicator = "大类资产配置实盘指标collection名"


@unique
class 基金定投CollectionName(str, Enum):
    backtest_signal = "基金定投回测信号collection名"
    backtest_indicator = "基金定投回测指标collection名"
    backtest_assess = "基金定投回测评级collection名"
    real_signal = "基金定投实盘信号collection名"
    real_indicator = "基金定投实盘指标collection名"


@unique
class EquipmentCollectionName(Enum):
    screens = 选股CollectionName
    timings = 择时CollectionName
    asset_allocation = 大类资产配置CollectionName
    aipman = 基金定投CollectionName


@unique
class 装备状态更新操作类型Enum(str, Enum):
    创建装备 = "创建装备"
    装备上线 = "装备上线"
    信号审核 = "信号审核"
    装备下线 = "装备下线"
    装备删除 = "装备删除"


@unique
class 市场风格(str, Enum):
    剧烈上涨 = "violent_ascent"
    平缓上涨 = "slight_ascent"
    宽幅震荡 = "violent_swinging"
    窄幅震荡 = "slight_swinging"
    平缓下跌 = "slight_decline"
    剧烈下跌 = "violent_decline"
