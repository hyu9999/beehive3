from enum import Enum, unique


@unique
class 趋势图分类(str, Enum):
    portfolio = "portfolio"  # 组合
    SHCompositeIndex = "000001"  # 上证综指
    HS300 = "000300"  # 沪深300
    SZCompositeIndex = "399001"  # 深证成指
    GEM = "399006"  # 创业板指
    Csi500 = "000905"  # 中证500
