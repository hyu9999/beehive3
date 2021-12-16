from pymongo import UpdateOne
from stralib import FastTdate

from app.crud.base import get_zvt_data_log_collection
from app.db.mongodb import db
from app.crud.zvt_data_log import get_zvt_data_logs


async def reset_zvt_data_log_state_task():
    """重置ZVT数据日志状态."""
    if not FastTdate.is_tdate():
        return None
    logs = await get_zvt_data_logs(db.client, limit=0, skip=0)
    update_list = []
    for log in logs:
        update_list.append(
            UpdateOne({"_id": log.id}, {"$set": {"state": "未完成"}})
        )
    if update_list:
        await get_zvt_data_log_collection(db.client).bulk_write(update_list)
