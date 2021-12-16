from asyncio import sleep
from datetime import datetime

from stralib import FastTdate

from app.schedulers.operation_data.func import update_strategy_calculate_datetime
from app.service.orders.order_trade import OrderTrade
from app.service.orders.order_trade_check import CheckOrder
from app.service.orders.order_trade_put import PutOrder


async def place_order_onstart_task():
    if OrderTrade.is_trade_time():
        await PutOrder.put_order()


async def check_order_onstart_task():
    if not FastTdate.is_tdate():
        return None
    await CheckOrder.realtime_check_order()


async def update_strategy_calculate_datetime_task():
    current_hour = datetime.now().hour
    if current_hour < 19 or current_hour > 23:
        return
    while True:
        if current_hour < 19 or current_hour > 23:
            return
        to_be_update_sid_list = await update_strategy_calculate_datetime()
        if len(to_be_update_sid_list) == 0:
            break
        await sleep(10 * 60)
