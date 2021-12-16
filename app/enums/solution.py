from enum import Enum


class SolutionTypeEnum(Enum):
    """
    解决方案类型
    """

    SCALE_UP = 0  # 同比例加仓
    SCALE_DOWN = 1  # 同比例减仓
    ROGUING = 2  # 去弱留强
    SIMPLE = 3  # 个股买卖
    NEW_STOCKS = 4  # 买入新股票
    CUSTOMIZE = 5  # 自定义


class SolutionStepEnum(Enum):
    START_FLAG = 0  # 开始标识
    CLOSE_OUT_LINE = 1  # 清仓线风险
    STOPLOSSTAKEPROFIT_CHANGEPOSITION_INDIVIDUALSTOCK = 2  # 止盈止损、调仓周期、个股风险
    UNDERWEIGHT = 3  # 仓位过轻
    OVERWEIGHT = 4  # 仓位过重
    NEW_STOCK = 5  # 买入新股票
    END_FLAG = 6  # 结束标识
