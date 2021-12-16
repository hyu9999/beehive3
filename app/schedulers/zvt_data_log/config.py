from app.schedulers.zvt_data_log.func import reset_zvt_data_log_state_task

reset_zvt_data_log_state_config = {
    "func": reset_zvt_data_log_state_task,
    "cron": {
        "id": "重置ZVT数据日志状态",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 0,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

