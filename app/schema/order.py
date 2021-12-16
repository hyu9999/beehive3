from datetime import datetime
from typing import Any, List

from pydantic import Field

from app.enums.log import 买卖方向
from app.enums.order import EntrustOrderStatus
from app.models.base.order import 股票基本信息, 股票订单基本信息
from app.models.order import Order
from app.models.rwmodel import PyObjectId, RWModel


class OrderInCreate(股票订单基本信息):
    username: str = Field(None, title="用户")
    task: Any = Field(None, title="任务 id")
    portfolio: PyObjectId = Field(..., title="组合")


class OrderInUpdate(Order):
    portfolio: PyObjectId = Field(None, title="组合")
    create_datetime: datetime = Field(None, title="订单创建时间")
    end_datetime: datetime = Field(None, title="订单结束时间")


class OrderInResponse(Order):
    pass


class TaskOrderInResponse(RWModel):
    """解决方案生成的任务信息"""

    id: Any = Field(..., description="任务编号")
    create_date: datetime = Field(..., description="任务创建日期")
    orders: List[Order] = Field(..., description="任务内的所有挂单")


class OrderInSolution(股票订单基本信息):
    """
    用于生成解决方案建议的股票订单
    """

    quantity: int = Field(..., description="交易数量")
    operator: 买卖方向 = Field(..., description="交易方向")
    price: float = Field(..., description="价格")


class SolutionOrderItem(OrderInSolution):
    """
    回测或解决方案中推荐的挂单
    """

    reason: str = Field(..., description="推荐下单原因")
    date: str = Field(..., description="下单日期")
    opinion: str = Field(None, description="推荐买入新股票入选理由")


class CreateEntrustOrderInResponse(RWModel):
    """
    委托订单响应
    """

    status: bool = Field(..., title="下单成功与否")
    explain: str = Field(..., title="当前订单状态说明")


class DeleteEntrustOrderInResponse(CreateEntrustOrderInResponse):
    data: dict = Field(..., title="数据")


class EntrustOrderInResponse(股票基本信息):
    """委托订单响应"""

    total_fee: float = Field(..., description="总交易费用")
    transfer_fee: float = Field(..., description="过户费")
    commission: float = Field(..., description="佣金")
    order_direction: 买卖方向 = Field(..., description="买卖方向")
    order_status: EntrustOrderStatus = Field(..., description="委托状态")
    order_quantity: int = Field(..., description="委托数量")
    filled_amt: float = Field(..., description="成交金额")
    order_date: str = Field(..., description="委托日期")
    order_time: str = Field(None, description="委托时间")
    trade_price: float = Field(..., description="成交价格")
    trade_volume: int = Field(..., description="成交数量")
    stamping: float = Field(..., description="印花税")
    trade_date: str = Field(None, description="成交日期")
    trade_time: str = Field(None, description="成交时间")
    settlement_fee: float = Field(..., description="结算费")
    order_id: str = Field(..., description="委托单号")
    order_price: float = Field(..., description="委托价格")
    position_change: float = Field(None, description="仓位变化")
