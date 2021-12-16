import asyncio
import copy
from collections import ChainMap
from datetime import datetime

import ujson
from pymongo import UpdateOne
from stralib import FastTdate

from app import settings
from app.core.errors import NotInTradingHour
from app.crud.order import get_order_by_order_id, get_orders, update_order_by_bulk
from app.crud.portfolio import get_portfolio_by_id, patch_portfolio_by_id
from app.crud.user import get_user, 创建消息
from app.db.mongodb import db
from app.enums.order import 订单状态
from app.enums.portfolio import 风险点状态
from app.enums.user import 消息分类, 消息类型
from app.extentions import logger
from app.global_var import G
from app.models.base.portfolio import 风险点信息
from app.models.rwmodel import PyObjectId
from app.schema.portfolio import PortfolioInUpdate
from app.schema.user import UserMessageInCreate
from app.service.orders.entrust_order import get_entrust_orders_recent_by_fund_id
from app.service.orders.order import update_from_trade_sys
from app.service.orders.order_trade import OrderTrade
from app.service.risks.detection import risk_detection


class CheckOrder(OrderTrade):
    """
    检测订单
    """

    @classmethod
    async def realtime_check_order(cls):
        """实时检测订单"""
        logger.info("[委托订单监控] 开始")
        if not FastTdate.is_tdate():
            raise Exception("当天为非交易日")
        while True:
            logger.debug("[委托订单监控] 轮训任务开始")
            # 交易时间刚过时, 未完成的订单不会立即被撤单, 所以需要等撤单完成后再更进行一次检测
            try:
                cls.check_trade_time()
            except NotInTradingHour:
                logger.error(f"[委托订单监控] 失败 非交易时间")
                try:
                    await cls.check_order()
                except Exception as e:
                    logger.error(f"[委托订单监控] 失败 {e}")
                await G.entrust_redis.flush()
                break
            try:
                await cls.check_order()
            except Exception as e:
                logger.error(f"[委托订单监控] 失败 {e}")
            logger.debug("[委托订单监控] 轮训任务结束 等待下次轮询")
            await asyncio.sleep(1)
        logger.info("[委托订单监控] 结束")

    @classmethod
    async def check_order(cls):
        """检测订单"""
        # 无组合则终止
        redis = G.entrust_redis
        portfolio_list = await redis.hgetall(cls.PORTFOLIO_HASH)
        if not portfolio_list:
            return
        pipe = await redis.pipeline()
        operations = []
        for portfolio_id in portfolio_list:
            # 组合不存在,删除redis相关信息
            portfolio = await get_portfolio_by_id(db.client, PyObjectId(portfolio_id))
            if not portfolio:
                await redis.hdel(cls.PORTFOLIO_HASH, portfolio_id)
                await redis.delete(portfolio_id)
                continue
            orders = await redis.hgetall(portfolio_id)
            if "task" in orders.keys():
                task = ujson.loads(orders.pop("task"))
            else:
                task = {}

            latest_orders_in_trade_sys = await get_entrust_orders_recent_by_fund_id(
                portfolio.fund_account[0].fundid
            )
            # 检查redis的订单是否已经处理完毕，如果处理完毕则删除redis内的无效数据并跳过这次循环
            if await cls.check_order_is_empty(orders, task, latest_orders_in_trade_sys):
                await redis.hdel(cls.PORTFOLIO_HASH, portfolio_id)
                await redis.delete(portfolio_id)
                continue
            # 处理正常下单
            if orders:
                await cls.deal_orders(
                    pipe, portfolio, orders, latest_orders_in_trade_sys
                )
            # 处理解决方案下单
            if task:
                await cls.deal_orders_by_task(
                    pipe, portfolio, copy.deepcopy(task), latest_orders_in_trade_sys
                )
            # 变更本地数据库订单状态
            changed_order_list = await cls.get_changed_orders(
                orders, task, latest_orders_in_trade_sys
            )
            operations = await cls.update_order_in_db(
                changed_order_list, latest_orders_in_trade_sys
            )
            operations.extend(operations)
        if operations:
            await update_order_by_bulk(db.client, operations, ordered=False)
        await pipe.execute()

    @classmethod
    async def update_order_in_db(cls, order_list, today_orders):
        operations = []
        if order_list:
            orders_in_database = await get_orders(
                db.client, {"order_id": {"$in": order_list}}
            )
            for order in orders_in_database:
                await update_from_trade_sys(order, today_orders[order.order_id])
                operations.append(UpdateOne({"_id": order.id}, {"$set": dict(order)}))
        return operations

    @classmethod
    async def deal_orders_by_task(cls, pipe, portfolio, task, latest_orders):
        """按task状态处理订单"""
        await cls.write_task_to_redis(pipe, portfolio, task, latest_orders)
        await cls.failed_task(portfolio, task, latest_orders)
        await cls.finish_task(portfolio, task, latest_orders)

    @classmethod
    async def write_task_to_redis(cls, pipe, portfolio, task, latest_orders):
        """写入任务"""
        task_orders = {}
        for order_id, old_status in task["orders"].items():
            new_status = latest_orders[order_id]["order_status"]
            if new_status != old_status:
                if new_status not in (
                    订单状态.waiting.value,
                    订单状态.in_progress.value,
                    订单状态.part_finished.value,
                ):
                    task_orders[order_id] = new_status
            else:
                task_orders[order_id] = old_status
            if new_status == 订单状态.all_finished:
                symbol_name = latest_orders[order_id]["symbol_name"]
                await cls.finished_order_action(order_id, symbol_name, portfolio)
        if task_orders != task["orders"]:
            task["orders"] = task_orders
            pipe.hmset(str(portfolio.id), "task", ujson.dumps(task))

    @classmethod
    async def failed_task(cls, portfolio, task, latest_orders):
        task_orders = task.get("orders", {})
        if [
            k
            for k, v in task_orders.items()
            if latest_orders[k]["order_status"] in (订单状态.failed, 订单状态.order_failed)
        ]:
            for risk in portfolio.risks:
                piu = PortfolioInUpdate(
                    **{
                        "risks": [
                            风险点信息(
                                **{
                                    "id": risk.id,
                                    "risk_type": risk.risk_type,
                                    "status": 风险点状态.unresolved,
                                }
                            )
                        ]
                    }
                )
                try:
                    await patch_portfolio_by_id(db.client, portfolio.id, piu)
                except Exception as e:
                    logger.warning(f"[更新风险状态失败]{e}")

    @classmethod
    async def finish_task(cls, portfolio, task, latest_orders):
        task_orders = task.get("orders", {})
        all_finished = (
            False
            if [
                k
                for k, v in task_orders.items()
                if latest_orders[k]["order_status"]
                in (订单状态.waiting, 订单状态.in_progress, 订单状态.part_finished)
            ]
            else True
        )
        if all_finished:
            for risk in portfolio.risks:
                piu = PortfolioInUpdate(
                    **{
                        "risks": [
                            风险点信息(
                                **{
                                    "id": risk.id,
                                    "risk_type": risk.risk_type,
                                    "status": 风险点状态.resolved,
                                }
                            )
                        ]
                    }
                )
                await patch_portfolio_by_id(db.client, portfolio.id, piu)
            # TODO: 机器人日志
            # await cls.write_robot_log_of_solution(portfolio, task["task_id"])
            await risk_detection(db.client, portfolio)

    @staticmethod
    async def check_order_is_empty(orders, task, latest_orders):
        """检测task中orders值是否为空"""
        task_orders = task.get("orders", None)
        if (not latest_orders) or (not any([task_orders, orders])):
            return True
        return False

    @classmethod
    async def deal_orders(cls, pipe, portfolio, orders, latest_orders):
        """处理订单"""
        portfolio_id = str(portfolio.id)
        for order_id, old_status in orders.items():
            # 订单写入redis的时间比推送订单到交易系统快，导致有时查询交易系统时查不到订单
            if order_id not in latest_orders.keys():
                continue
            new_status = latest_orders[order_id]["order_status"]
            if new_status != old_status:  # 状态变更：修改redis订单状态
                pipe.hset(portfolio_id, order_id, new_status)
            if new_status not in (
                订单状态.waiting,
                订单状态.in_progress,
                订单状态.part_finished,
            ):  # 订单结束：删除redis记录并进行风险检测
                pipe.hdel(portfolio_id, order_id)
                await risk_detection(db.client, portfolio)
            if new_status == 订单状态.all_finished:  # 订单全部成交后的动作：发送消息
                symbol_name = latest_orders[order_id]["symbol_name"]

                await cls.finished_order_action(order_id, symbol_name, portfolio)

    @classmethod
    async def finished_order_action(cls, order_id, symbol_name, portfolio):
        """订单全部成交后的动作"""
        hm = datetime.now().strftime("%H:%M")
        content = f"{hm} 您的组合 【{portfolio.name}】——【{symbol_name}】交易成功"
        url = f"""
        <a href="{settings.host}#/portfolio/{portfolio.id}">详情</a>"""
        # TODO 发送微信提醒未实现
        await cls.send_user_msg(portfolio, order_id, content)

    @staticmethod
    async def send_wechat_msg(portfolio, content, url=None):
        """发送微信提醒"""
        open_id = portfolio.user.open_id
        send_flag = portfolio.user.send_flag
        if open_id and send_flag:
            content = f"""{content}{url}"""
            try:
                # TODO: msg client
                # app.msg_client.send_text(open_id, content)
                pass
            except Exception as e:
                logger.warning(f"[发送消息失败]{e}")

    @staticmethod
    async def send_user_msg(portfolio, order_id, content):
        """发送用户消息"""
        order = await get_order_by_order_id(db.client, order_id)
        user = await get_user(db.client, order.username)
        kwargs = {
            "title": f"交易成功",
            "content": content,
            "category": 消息分类.portfolio,
            "msg_type": 消息类型.task_finished,
            "username": f"{portfolio.username}",
            "data_info": f"{portfolio.id}",
        }
        await 创建消息(db.client, user, UserMessageInCreate(**kwargs))

    @classmethod
    async def get_changed_orders(cls, orders, task, today_orders):
        """获取全部状态发生变化的订单：普通订单和任务订单"""
        task_orders = task.get("orders", {}) if task else {}
        order_dict = ChainMap(orders, task_orders)
        order_list = [
            k for k, v in order_dict.items() if today_orders[k]["order_status"] != v
        ]
        return order_list
