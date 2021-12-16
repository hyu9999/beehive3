from datetime import datetime

from pydantic import Field

from app.enums.log import 买卖方向, 日志分类
from app.enums.order import EntrustOrderStatus
from app.enums.stock import 出入金类型
from app.models.base.stock import 股票基本信息
from app.models.rwmodel import RWModel


class 股票交易日志基本信息(股票基本信息):
    sno: str = Field(None, title="流水号", description="流水号, 单日的唯一流水号")
    order_quantity: str = Field(None, title="委托数量")
    order_id: str = Field(None, title="订单id")
    order_time: str = Field(None, title="委托时间")
    order_direction: 买卖方向 = Field(None, title="买卖方向")
    order_price: float = Field(None, title="买卖方向")
    order_volume: int = Field(None, title="委托数量")
    # 不同交易系统订单状态不同，这里只记录值，不设置对应关系
    order_status: str = Field(None, title="委托状态")
    trade_date: str = Field(None, title="成交日期")
    trade_time: str = Field(None, title="成交时间")
    trade_price: float = Field(None, title="成交价格")
    trade_volume: float = Field(None, title="成交数量")
    stkeffect: int = Field(None, title="证券变动")
    stock_quantity: int = Field(None, title="证券余额")
    fundeffect: float = Field(None, title="资金变动")
    fundbal: float = Field(None, title="资金余额")
    degestid: str = Field(None, title="业务标志")
    stamping: float = Field(None, title="印花税")  # 印花税
    transfer_fee: float = Field(None, title="过户费")  # 过户费
    commission: float = Field(None, title="佣金")  # 佣金
    total_fee: float = Field(None, title="总费用")  # 总费用
    filled_amt: float = Field(None, title="成交金额")
    settlement_fee: float = Field(None, title="结算费")
    order_date: str = Field(None, title="委托日期")
    # 操作类型，为兼容ability数据结构，补充ttype值，
    # ability数据定义见https://shimo.im/doc/CKTCKGjxOscDK97y?r=5RYN8D
    ttype: str = Field(None, title="操作类型", regex="^[1-47]$")


class 资金账户基本信息(RWModel):
    fund_id: str = Field("", description="资金账户")
    capital: float = Field(0, description="初始资产")
    total_capital: float = Field(0, description="总资产")
    fund_balance: float = Field(0, description="资金余额")
    fund_available: float = Field(0, description="可用现金")
    fund_depositable: float = Field(0, description="可取余额")
    market_value: float = Field(0, description="市值")
    total_profit: float = Field(0, description="总收益")
    total_profit_rate: float = Field(0, description="总收益率")


class 账户持仓基本信息(股票基本信息):
    fund_id: str = Field(None, description="资金账号")
    stock_quantity: int = Field(0, description="持仓量")
    stock_available_quantity: int = Field(0, description="可用量")
    buy_price: float = Field(0, description="持仓成本")
    realtime_price: float = Field(0, description="当前价格")
    float_profit: float = Field(0, description="利润")
    buy_date: datetime = Field(None, description="首次持有日期")
    fund_in_transit: float = Field(0, description="在途资金")
    fund_freezing: float = Field(0, description="冻结资金")
    share_cost_price: float = Field(0, description="证券持仓成本")
    market_value: float = Field(0, description="市值")
    profit_rate_stock: float = Field(0, description="个股盈亏比率")


class 错误日志基本信息(RWModel):
    category: 日志分类 = Field(None, title="日志分类")
    status: str = Field(None, title="状态")
    content: str = Field(None, title="日志内容")


class 出入金记录(RWModel):
    cash: float = Field(..., gt=0, title="现金")
    cash_type: 出入金类型 = Field(..., title="出入金类型")
    create_date: datetime = Field(None, title="创建日期")
