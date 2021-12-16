"""
定义证券资源
"""
#  Copyright (c) 2019. 西安金牛创智科技有限公司

from enum import Enum

from datetime import date, time, datetime
from pydantic import BaseModel, Field


class 证券交易所(str, Enum):
    上交所 = "1"
    上海 = "1"
    上证 = "1"
    CNSESH = "CNSESH"
    深交所 = "0"
    深圳 = "0"
    深证 = "0"
    CNSESZ = "CNSESZ"
    nan = "nan"  # 为支持没有信号的情况


class 币种(Enum):
    人民币 = 1
    港币 = 2
    美元 = 3


class 委托类别(str, Enum):
    买 = "0"
    卖 = "1"
    撤单 = "3"


class 证券类型(str, Enum):
    股票 = "股票"
    基金 = "基金"
    债券 = "债券"
    资管 = "资管"
    理财 = "理财"


class 基金类型(str, Enum):
    封闭式基金 = "封闭式基金"
    开放式基金 = "开放式基金"


class 基金(BaseModel):
    基金代码: str
    基金类型: 基金类型
    基金名称: str
    基金净值: float


class 股票(BaseModel):
    交易所: 证券交易所
    证券代码: str = Field(..., regex=r"^\d{6}$")
    证券名称: str = Field(..., max_length=4)


class 委托类型(str, Enum):
    本方最优价格 = "S"
    对手方最优价格 = "Q"
    全额成交或撤单 = "V"
    最优五档即时成交剩余转限价 = "R"
    买卖 = "0"
    即时成交剩余撤销 = "T"
    最优五档即时成交剩余撤销 = "U"
    限价委托 = "d"
    定价委托 = "b"
    互报成交确认委托 = "e"
    确认委托 = "c"
    申购 = "3"


class 持仓(BaseModel):
    """
    参数名	类型	最大长度	默认值	中文名	描述
    exchange_type	String	4		交易类别
    【限制字典子项：1-上海
    H-深Ｂ
    D-沪Ｂ
    2-深圳
    A-特转B
    9-特转A】

    数据字典(243)

    stock_account	String	11		证券账号
    stock_code	String	16		证券代码
    stock_name	String	32		证券名称
    current_amount	Integer	10		当前数量
    enable_amount	Integer	10		可用数量
    last_price	Float	18.3		最新价
    cost_price	Float	11.4		成本价
    income_balance	Float	16.2		盈亏金额
    market_value	Float	16.2		证券市值
    position_str	String	100		定位串
    money_type	String	3		币种类别
    day_income_balance	Float	16.2		日盈亏金额
    由后台服务计算，当日盈亏数据仅为参考值，不作为具体的投资参考意见
    """

    证券交易所: 证券交易所
    证券账号: str
    证券代码: str
    证券名称: str
    当前数量: int
    可用数量: int
    最新价: float
    成本价: float
    盈亏金额: float
    证券市值: int
    币种类别: 币种
    日盈亏金额: float


class 成交流水(BaseModel):
    交易日期: date
    流水序号: str
    交易所: 证券交易所
    证券账号: str
    证券代码: str
    证券名称: str
    买卖方向: 委托类别
    成交价格: float
    成交时间: time
    委托编号: int
    发生数量: int
    成交金额: float


class 委托状态(str, Enum):
    已成 = "8"
    未报 = "0"
    已报待撤 = "3"
    待报 = "1"
    已撤 = "6"
    已报 = "2"
    废单 = "9"
    部成 = "7"
    部成待撤 = "4"


class 委托流水(BaseModel):
    交易日期: date
    委托编号: str
    交易所: 证券交易所
    证券账号: str
    证券代码: str
    证券名称: str
    买卖方向: 委托类别
    委托价格: float
    成交数量: int
    成交时间: time
    委托数量: int
    成交金额: float
    申请编号: int
    委托日期: date
    委托时间: time
    申报时间: time
    委托类别: 委托类别
    委托状态: 委托状态


class 资金流水(BaseModel):
    流水序号: str
    成交日期: date
    业务名称: str
    发生金额: float
    后资金额: float
    币种类别: 币种
    发生数量: int


class 银行账户(BaseModel):
    币种类别: 币种
    银行代码: str = 0
    银行名称: str
    银行账号: str
    客户账号: str
    银行密码输入控制: str


class 银行委托状态(str, Enum):
    待冲正 = "7"
    正报 = "P"
    已确认 = "Q"
    作废 = "3"
    待报 = "A"
    已冲正 = "8"
    待确定 = "x"
    成功 = "2"
    已报 = "1"
    未报 = "0"
    待撤 = "4"
    撤销 = "5"


class 银行转账流水(BaseModel):
    银行代码: str
    银行名称: str
    发生金额: float
    委托编号: str
    请求状态: 银行委托状态
    委托时间: time
    废单原因: str
    转换机名字: str
    币种类别: 币种
    发起方: str  # 0=券商, 1=银行
