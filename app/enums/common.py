from enum import Enum, unique


@unique
class 回测评级数据集(str, Enum):
    整体评级 = "整体评级"
    训练集评级 = "训练集评级"
    测试集评级 = "测试集评级"


@unique
class 数据库排序(int, Enum):
    正序 = 1
    倒序 = -1


@unique
class 保密文件类型(str, Enum):
    装备源代码 = "装备源代码"


@unique
class 公共文件类型(str, Enum):
    用户头像 = "用户头像"
    机器人头像 = "机器人头像"


@unique
class 操作方向(str, Enum):
    买入 = "买入"
    卖出 = "卖出"
    保持不变 = "保持不变"


class DateType(str, Enum):
    """日期类型"""

    ALL = 0  # 全部
    YEAR = 1  # 年
    MONTH = 2  # 月
    WEEK = 3  # 周
    DAY = 4  # 日
    CUSTOM = 5  # 自定义


class FormatType(str, Enum):
    """格式化类型"""

    列表 = "list"
    字典 = "dict"


class DataSourceType(str, Enum):
    """数据来源类型"""

    mongodb = "mongodb"
    redis = "redis"


class 数据库操作Enum(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    RETRIEVE = "RETRIEVE"


@unique
class 产品分类(str, Enum):
    portfolio = "portfolio"
    robot = "robot"
    equipment = "equipment"


@unique
class 中文产品分类(str, Enum):
    portfolio = "组合"
    robot = "机器人"
    equipment = "装备"
