from datetime import datetime

from pymongo import UpdateOne

from app.crud.stock import bulk_write_stock
from app.db.mongodb import db
from app.dec.scheduler import print_execute_time
from app.service.stocks.stock import get_stock_list_from_stralib


@print_execute_time
async def update_stock_info_task():
    """更新股票信息列表"""
    current_dt = datetime.utcnow()
    stock_info_list = get_stock_list_from_stralib()
    bulk_list = []
    for stock_info in stock_info_list:
        stock_info["update_time"] = current_dt
        bulk_list.append(
            UpdateOne(
                {"symbol": stock_info["symbol"], "exchange": stock_info["exchange"]},
                {"$set": stock_info},
                upsert=True,
            )
        )
    await bulk_write_stock(db.client, bulk_list)
