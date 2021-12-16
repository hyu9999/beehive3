from datetime import datetime, timedelta
from typing import Dict, List

import bson
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from stralib import FastTdate

from app import settings
from app.core.errors import NotInTradingHour, OrderAuthError
from app.crud.order import create_order, update_order_by_bulk
from app.crud.portfolio import get_portfolio_by_id, update_risk_status
from app.crud.user import 创建消息
from app.db.mongodb import db
from app.enums.order import 订单状态
from app.enums.portfolio import 风险点状态
from app.enums.user import 消息分类, 消息类型
from app.global_var import G
from app.models.base.order import 股票订单基本信息
from app.models.order import Order
from app.outer_sys.hq import get_security_info, get_security_meta, get_security_price
from app.schema.order import CreateEntrustOrderInResponse, OrderInCreate
from app.schema.portfolio import PortfolioInResponse, PortfolioRiskStatusInUpdate
from app.schema.trade_system import TradeInResponse
from app.schema.user import User, UserMessageInCreate
from app.service.orders.entrust_order import get_task_orders
from app.service.orders.order_trade import OrderTrade
from app.utils.datetime import get_utc_now


class PutOrder(OrderTrade):
    """
    下单
    """

    @staticmethod
    async def put_order_to_trade_sys(
        order: Dict, portfolio: PortfolioInResponse
    ) -> TradeInResponse:
        """下单请求推送到模拟交易系统."""

        # 解决方案生成的订单价格为-1
        if float(order["price"]) == float(-1.0):
            security = await get_security_price(order["symbol"], order["exchange"])
            order["price"] = float(security.current)
        if order.get("create_datetime"):
            create_dt = order["create_datetime"] + timedelta(hours=8)
        else:
            create_dt = get_utc_now() + timedelta(hours=8)
        kwargs = {
            "symbol": order["symbol"],
            "exchange": "SH" if order["exchange"] == "1" else "SZ",
            "order_price": order["price"],
            "order_direction": order["operator"],
            "order_quantity": order["quantity"],
            "order_date": f"{create_dt:%Y%m%d}",
            "order_time": f"{create_dt:%H:%M:%S}",
        }
        return await G.trade_system.order_input(
            portfolio.fund_account[0].fundid, **kwargs
        )

    @classmethod
    async def put_order(cls):
        """
        对数据库中等待下单的委托进行下单, 并跟踪检测
        """
        cls.check_trade_time()
        task_orders = await get_task_orders()
        operations = []
        for order_group in task_orders:
            task_id = order_group["_id"].get("task_id")
            portfolio = await get_portfolio_by_id(
                db.client, order_group["_id"]["portfolio_id"]
            )
            orders = []
            for order_obj in order_group["orders"]:
                # 向模拟账户平台提交委托订单
                tir = await cls.put_order_to_trade_sys(order_obj, portfolio)
                # 如果提交委托订单成功，更新订单状态为处理中
                if tir.flag:
                    assert order_obj["status"] in (
                        订单状态.waiting.value,
                        订单状态.order_failed.value,
                    )
                    order_obj["status"] = 订单状态.in_progress.value
                    order_obj["order_id"] = tir.data["order_id"]
                    orders.append(Order(**order_obj))
                else:
                    assert order_obj["status"] in (
                        订单状态.waiting.value,
                        订单状态.order_failed.value,
                    )
                    order_obj["status"] = 订单状态.order_failed.value
                    # 如果已加入任务队列 更新组合中的风险点状态为未解决
                    if task_id:
                        for risk in portfolio.risks:
                            await update_risk_status(
                                db.client,
                                portfolio,
                                [
                                    PortfolioRiskStatusInUpdate(
                                        id=risk.id, status=风险点状态.unresolved
                                    )
                                ],
                            )
                # 更新数据库中 order 的状态和订单 id
                operations.append(
                    UpdateOne({"_id": order_obj["_id"]}, {"$set": order_obj})
                )
                # TODO: 发送文章到社区
                # 加入检测队列, 实时更新订单状态和任务
                await cls.insert_to_monitor_pool(portfolio, orders, task_id)
            if operations:
                await update_order_by_bulk(db.client, operations)


async def entrust_orders(
    conn: AsyncIOMotorClient,
    user: User,
    portfolio: PortfolioInResponse,
    orders: List[股票订单基本信息],
    is_task: bool = False,
):
    """委托下单"""
    if not user.username == portfolio.username:
        raise OrderAuthError
    # 验证订单中股票价格精度和数量是否正确
    for order in orders:
        security = await get_security_meta(order.symbol, order.exchange)
        if len(str(order.price).split(".")) == 2:
            if security.precision < len(str(order.price).split(".")[-1]):
                return CreateEntrustOrderInResponse(
                    status=False,
                    explain=f"订单中证券`{order.symbol}.{order.exchange}`的价格精度错误。",
                )
        if order.quantity % security.min_unit != 0:
            return CreateEntrustOrderInResponse(
                status=False, explain=f"订单中证券`{order.symbol}.{order.exchange}`的购买数量错误。"
            )
    if is_task:
        task_id = bson.ObjectId()
        # 刷新组合风险点状态
        for risk in portfolio.risks:
            # 若组合中存在已确认的风险点 且 该风险点为个股风险 且 该个股风险与新建委托单中的股票相同时，重新标记该风险点为解决中
            if (
                risk.symbol in [order.symbol for order in orders]
                and risk.status == 风险点状态.confirmed
            ):
                await update_risk_status(
                    conn,
                    portfolio,
                    [PortfolioRiskStatusInUpdate(id=risk.id, status=风险点状态.solving)],
                )
            # 若组合中的风险不是个股风险 且 风险状态为已确认，重新标记该风险点为解决中
            elif not risk.symbol and risk.status == 风险点状态.confirmed:
                await update_risk_status(
                    conn,
                    portfolio,
                    [PortfolioRiskStatusInUpdate(id=risk.id, status=风险点状态.solving)],
                )
        # 写入用户消息表：解决方案已生成
        kwargs = {
            "title": f'"{portfolio.name}" 已生成委托订单',
            "content": f"已按照解决方案生成委托订单",
            "category": 消息分类.portfolio,
            "msg_type": 消息类型.order_generated,
            "username": portfolio.username,
            "data_info": f"{portfolio.id}",
        }
        await 创建消息(conn, user, UserMessageInCreate(**kwargs))
        # TODO: 发送文章到社区
    else:
        # 普通下单，非交易时间不允许下单
        if not (
            FastTdate.is_tdate()
            and settings.allow_pending_order_time
            < datetime.now().time()
            < settings.close_market_time
        ):
            return CreateEntrustOrderInResponse(status=False, explain="非交易时间段，无法进行交易")
        task_id = None
    # 本地记录订单信息
    for order in orders:
        order_dict = {}
        order_dict.update(dict(order))
        order_dict.update(
            dict(username=user.username, status=订单状态.waiting, task=task_id)
        )
        order_dict.update(dict(fund_id=portfolio.fund_account[0].fundid))
        security = await get_security_info(order.symbol, order.exchange)
        order_dict.update(dict(symbol_name=security.symbol_name))
        order_dict.update(dict(portfolio=portfolio.id))
        order_obj = OrderInCreate(**order_dict)
        await create_order(conn, order_obj)
    # 下单
    try:
        await PutOrder.put_order()
    except NotInTradingHour:
        return CreateEntrustOrderInResponse(
            status=False, explain=f"当前不在交易时间，系统已记录，开盘后自动下单."
        )
    return CreateEntrustOrderInResponse(status=True, explain="已经成功下单")
