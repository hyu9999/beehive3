from pydantic import Field

from app.enums.log import 买卖方向
from app.enums.order import 订单状态
from app.models.base.stock import 股票基本信息


class 股票订单基本信息(股票基本信息):
    order_id: str = Field(None, title="订单ID")
    fund_id: str = Field(None, title="资金账户ID")
    status: 订单状态 = Field(None, title="挂单当前状态")
    finished_quantity: int = Field(None, title="挂单交易成功的数量")
    average_price: float = Field(None, title="委托成交均价")
    quantity: int = Field(None, title="交易数量")
    operator: 买卖方向 = Field(None, title="交易方向")
    price: float = Field(None, title="价格")


