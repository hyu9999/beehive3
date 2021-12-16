from pymongo import ReplaceOne

from app.crud.base import get_portfolio_collection, get_stock_log_collection
from app.db.mongodb import db
from app.enums.portfolio import 组合状态, 数据同步方式
from app.service.datetime import str_of_today
from app.service.orders.entrust_order import close_order
from app.service.orders.order_trade_check import CheckOrder
from app.service.orders.order_trade_put import PutOrder


async def close_order_task():
    await close_order()


async def place_order_task():
    await PutOrder.put_order()


async def check_order_task():
    await CheckOrder.realtime_check_order()


async def check_order_bills_task():
    """核对股票订单"""
    queryset = get_portfolio_collection(db.client).find({"status": 组合状态.running, "sync_type": 数据同步方式.auto})
    today = str_of_today()
    async for portfolio in queryset:
        data_operator = AccountAbilityData(db.client, portfolio)
        data = await data_operator.fetch_log(today, today).get(today, [])
        replace_list = []
        for item in data:
            queryset = get_stock_log_collection(db.client).find({"order_id": item.get("order_id")})
            item["portfolio"] = portfolio
            item["order_direction"] = item["order_direction_ex"]
            item["order_status"] = str(item["order_status"])
            cnt = await get_stock_log_collection(db).count_documents({"order_id": item.get("order_id")})
            if cnt == 1:
                continue
            if cnt > 1:
                queryset.delete()
            obj = ReplaceOne(item, item)
            replace_list.append(obj)
        if replace_list:
            await get_stock_log_collection(db.client).bulk_write(replace_list)
