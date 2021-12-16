from datetime import datetime

from hq2redis import HQSourceError, SecurityNotFoundError
from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.order import get_orders
from app.crud.portfolio import update_risk_status
from app.enums.order import 订单状态
from app.enums.portfolio import 风险点状态
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.outer_sys.hq import get_security_info
from app.schema.order import OrderInResponse
from app.schema.portfolio import PortfolioRiskStatusInUpdate
from app.service.risks.detection import risk_detection


async def update_order_stock_name(orders):
    """获取订单内的股票名称"""
    for order in orders:
        try:
            security = await get_security_info(order["symbol"], order["exchange"])
            order["symbol_name"] = security.symbol_name
        except (HQSourceError, SecurityNotFoundError) as e:
            raise Exception("获取订单内的股票名称失败") from e
    return orders


async def update_from_trade_sys(order: OrderInResponse, data) -> OrderInResponse:
    """
    从mogu返回的数据更新order
    Parameters
    ----------
    data    outer_sys/trade_system/pt/output_tuple.ORDER_RECORD
    """
    order.status = data["order_status"]
    order.finished_quantity = data["trade_volume"]
    order.average_price = data["trade_price"]
    order.symbol_name = data["symbol_name"]
    trade_time = data.get("trade_time", "")
    trade_date = data.get("trade_date", "")
    if trade_date and trade_time:
        order.end_datetime = datetime.strptime(trade_date[:19], "%Y-%m-%dT%H:%M:%S")
    return order


async def update_task_status(conn: AsyncIOMotorClient, task_id: PyObjectId, portfolio: Portfolio):
    """更新任务状态"""
    """
    如果不存在等待、处理以及部分成交的订单，将风险点全部置为已解决，然后进行一次风险检测
    """
    queryset = await get_orders(conn, {"task": task_id})
    all_status = [x.status for x in queryset]
    if not [x for x in all_status if x in [订单状态.waiting, 订单状态.in_progress, 订单状态.part_finished]]:
        risks = [PortfolioRiskStatusInUpdate(id=x.id, status=风险点状态.unresolved) for x in portfolio.risks]
        await update_risk_status(conn, portfolio, risks)
        await risk_detection(conn, portfolio)
