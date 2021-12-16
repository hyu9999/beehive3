from app.schedulers.message.func import send_equipment_signal_message_task

send_equipment_signal_message_config = {
    "func": send_equipment_signal_message_task,
    "cron": {
        "trigger": "cron",
        "id": "每日装备信号出现后，通知订阅或者创建该装备的用户",
        "day_of_week": "0-4",
        "hour": 21,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}