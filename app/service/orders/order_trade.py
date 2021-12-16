from datetime import datetime, time
from typing import List, Optional

import ujson
from stralib import FastTdate

from app.core.errors import NotInTradingHour
from app.global_var import G
from app.models.order import Order
from app.schema.portfolio import PortfolioInResponse


class OrderTrade:
    """
    订单交易
    """

    PORTFOLIO_HASH = "portfolio"

    @staticmethod
    def is_trade_time():
        """判断是否为交易时间"""
        return not (
            FastTdate.is_closed()
            or not (time(9, 30) < datetime.now().time() < time(15))
        )

    @classmethod
    def check_trade_time(cls):
        """检查是否为可挂单时间."""
        if FastTdate.is_closed() or not (
            time(9, 15) < datetime.now().time() < time(15)
        ):
            raise NotInTradingHour

    @classmethod
    async def insert_to_monitor_pool(
        cls,
        portfolio: PortfolioInResponse,
        orders: List[Order],
        task_id: Optional[str] = None,
    ):
        """
        下单时将委托添加到监测池里, 对于从解决方案生成的委托, 同时加入任务字段
        Parameters
        ----------
        portfolio   组合
        task_id     任务id
        orders      委托订单可迭代对象
        entrust_cache 委托订单redis
        """
        redis = G.entrust_redis
        pipeline = await redis.pipeline()
        portfolio_id = str(portfolio.id)
        portfolio = await redis.hget(cls.PORTFOLIO_HASH, portfolio_id, encoding="utf8")
        if not portfolio:
            pipeline.hset(cls.PORTFOLIO_HASH, portfolio_id, "1")

        if task_id:
            task_info = {"task_id": str(task_id)}
            task_orders = {}
            for order in orders:
                task_orders[order.order_id] = order.status
            task_info["orders"] = task_orders
            pipeline.hmset(portfolio_id, "task", ujson.dumps(task_info))
        else:
            for order in orders:
                pipeline.hset(portfolio_id, order.order_id, order.status.value)
        if pipeline is not None:
            await pipeline.execute()
