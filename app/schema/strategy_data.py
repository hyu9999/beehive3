import importlib
import inspect
from datetime import datetime
from typing import Union

from pydantic import Field

from app.models.rwmodel import RWModel
from app.models.strategy_data import (
    择时回测信号,
    择时回测指标,
    择时回测评级,
    择时实盘信号,
    择时实盘指标,
    选股回测信号,
    选股回测指标,
    选股回测评级,
    选股实盘信号,
    选股实盘指标,
    大类资产配置回测信号,
    大类资产配置回测指标,
    大类资产配置回测评级,
    大类资产配置实盘信号,
    大类资产配置实盘指标,
    基金定投回测信号,
    基金定投回测指标,
    基金定投回测评级,
    基金定投实盘信号,
    基金定投实盘指标,
    机器人回测指标,
    机器人回测信号,
    机器人回测评级,
    机器人实盘信号,
    机器人实盘指标,
)


class 择时回测信号InCreate(择时回测信号):
    pass


class 择时回测指标InCreate(择时回测指标):
    pass


class 择时回测评级InCreate(择时回测评级):
    pass


class 择时实盘信号InCreate(择时实盘信号):
    pass


class 择时实盘指标InCreate(择时实盘指标):
    pass


class 选股回测信号InCreate(选股回测信号):
    pass


class 选股回测指标InCreate(选股回测指标):
    pass


class 选股回测评级InCreate(选股回测评级):
    pass


class 选股实盘信号InCreate(选股实盘信号):
    pass


class 选股实盘指标InCreate(选股实盘指标):
    pass


class 大类资产配置回测信号InCreate(大类资产配置回测信号):
    pass


class 大类资产配置回测指标InCreate(大类资产配置回测指标):
    pass


class 大类资产配置回测评级InCreate(大类资产配置回测评级):
    pass


class 大类资产配置实盘信号InCreate(大类资产配置实盘信号):
    pass


class 大类资产配置实盘指标InCreate(大类资产配置实盘指标):
    pass


class 基金定投回测信号InCreate(基金定投回测信号):
    pass


class 基金定投回测指标InCreate(基金定投回测指标):
    pass


class 基金定投回测评级InCreate(基金定投回测评级):
    pass


class 基金定投实盘信号InCreate(基金定投实盘信号):
    pass


class 基金定投实盘指标InCreate(基金定投实盘指标):
    pass


class 机器人回测指标InCreate(机器人回测指标):
    pass


class 机器人回测信号InCreate(机器人回测信号):
    pass


class 机器人回测评级InCreate(机器人回测评级):
    pass


class 机器人实盘信号InCreate(机器人实盘信号):
    pass


class 机器人实盘指标InCreate(机器人实盘指标):
    pass


def get_union_schema():
    def is_sub_class(value):
        if inspect.isclass(value) and issubclass(value, RWModel):
            return True
        else:
            return False

    ip_module = importlib.import_module(__name__)
    classes = inspect.getmembers(ip_module, is_sub_class)
    exec("from typing import Union")
    return eval(f"Union{[x for x,_ in classes]}")


StrategyInCreate = Union[
    择时实盘信号InCreate,
    择时实盘指标InCreate,
    择时回测信号InCreate,
    择时回测指标InCreate,
    择时回测评级InCreate,
    选股实盘信号InCreate,
    选股实盘指标InCreate,
    选股回测信号InCreate,
    选股回测指标InCreate,
    选股回测评级InCreate,
    大类资产配置实盘信号InCreate,
    大类资产配置实盘指标InCreate,
    大类资产配置回测信号InCreate,
    大类资产配置回测指标InCreate,
    大类资产配置回测评级InCreate,
    基金定投实盘信号InCreate,
    基金定投实盘指标InCreate,
    基金定投回测信号InCreate,
    基金定投回测指标InCreate,
    基金定投回测评级InCreate,
    机器人实盘指标InCreate,
    机器人实盘信号InCreate,
    机器人回测指标InCreate,
    机器人回测信号InCreate,
    机器人回测评级InCreate,
]


class 策略数据InCreate(RWModel):
    SYMBOL: str
    EXCHANGE: str
    TDATE: datetime
    TCLOSE: float
    SCORE: float = Field(1)
