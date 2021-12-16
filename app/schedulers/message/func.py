from datetime import datetime

from app.crud.base import get_user_collection
from app.db.mongodb import db
from app.service.datetime import get_early_morning
from app.service.message.send import get_all_equipment_signals, get_equipment_signal_by_user, send_message


async def send_equipment_signal_message_task(filters: dict = None, tdate: datetime = None):
    """群发消息(装备信号)给用户"""
    tdate = tdate or get_early_morning()
    filters = filters or {"send_flag": True}
    users = get_user_collection(db.client).find(filters)
    all_signals = await get_all_equipment_signals(db.client, tdate)
    async for user in users:
        content = await get_equipment_signal_by_user(db.client, user, tdate, all_signals)
        await send_message(user, content, tdate) if content else None
