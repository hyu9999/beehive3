from typing import Dict, List

from stralib import FastTdate

from app.crud.base import get_order_collection
from app.crud.order import get_orders, update_order_by_id
from app.db.mongodb import db
from app.enums.order import 订单状态
from app.extentions import logger
from app.global_var import G
from app.schema.order import EntrustOrderInResponse, OrderInUpdate
from app.service.datetime import str_of_today
from app.service.risks import risk


async def get_task_orders():
    """获取任务订单列表"""
    pipeline = [
        {"$match": {"status": 订单状态.waiting}},
        {
            "$group": {
                "_id": {"task_id": "$task", "portfolio_id": "$portfolio"},
                "orders": {"$push": "$$ROOT"},
            }
        },
    ]
    rows = (
        await get_order_collection(db.client).aggregate(pipeline).to_list(length=None)
    )
    return rows


async def cancel_in_progress_orders():
    """更改处理中的委托订单状态为已取消"""
    orders_in_progress = await get_orders(db.client, {"status": 订单状态.in_progress})
    for order in orders_in_progress:
        order.status = 订单状态.canceled
        await update_order_by_id(db.client, order.id, OrderInUpdate(**dict(order)))


async def close_order():
    """
    关闭当日正在委托的订单
    每个交易日收盘后对当日所有处理中的订单将其定为已取消, 并将所有今天所有的风险点置为已解决
    """
    t_date = str_of_today()
    # 如果今天不是交易日则直接返回，不进行风险点重置
    if not FastTdate.is_tdate(t_date):
        return
    await cancel_in_progress_orders()
    await risk.finish_portfolio_risks()
    logger.warning("risk重置成功")


async def get_entrust_orders_recent_by_fund_id(fund_id: str) -> Dict[str, dict]:
    """
    查询用户当日所有委托订单
    Parameters
    ----------
    fund_id:    资金账户ID

    Returns
    -------
        Dict[order_id]: outer_sys/trade_system/output_tuple/ORDER_RECORD
    """
    start_date = stop_date = str_of_today()
    op_flag = 1  # 1表示委托订单
    tir = await G.trade_system.get_order_record(
        fund_id,
        start_date=start_date,
        stop_date=stop_date,
        op_flag=op_flag,
    )
    if tir.flag:
        return {order["order_id"]: order for order in tir.data}
    return {}


async def get_entrust_orders(
    portfolio,
    start_date,
    stop_date,
    op_flag,
) -> List[EntrustOrderInResponse]:
    """
    获取组合的委托单记录
    """
    tir = await G.trade_system.get_order_record(
        portfolio.fund_account[0].fundid,
        start_date=start_date,
        stop_date=stop_date,
        op_flag=op_flag,
    )
    if not tir.flag:
        return []
    return [EntrustOrderInResponse(**d) for d in tir.data]


async def get_recent_entrust_orders(
    conn,
    portfolio,
    op_flag,
) -> List[EntrustOrderInResponse]:
    """
    获取组合最近的委托单记录
    """
    orders = await get_entrust_orders(
        portfolio, start_date=str_of_today(), stop_date=str_of_today(), op_flag=op_flag
    )
    if not orders:
        tir = await G.trade_system.get_order_record(
            portfolio.fund_account[0].fundid,
            op_flag=op_flag,
        )
        orders = tir.data
        if not orders:
            return []
        orders.sort(key=lambda x: x["trade_date"], reverse=True)
        recent_day = orders[0]["trade_date"]
        return [
            EntrustOrderInResponse(**order)
            for order in orders
            if order["trade_date"] == recent_day
        ]
    else:
        return orders
