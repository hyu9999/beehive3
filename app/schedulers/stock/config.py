from .func import update_stock_info_task

update_stock_info_config = {
    "func": update_stock_info_task,
    "cron": {
        "trigger": "cron",
        "id": "更新股票信息列表",
        "day_of_week": "0-6",
        "hour": 9,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
