from app.schedulers.publish.func import write_strategy_publish_log_task, check_strategy_data_task

write_strategy_publish_log_config = {
    "func": write_strategy_publish_log_task,
    "cron": {
        "id": "策略发布数据写入",
        "trigger": "cron",
        "day_of_week": "0-6",
        "hour": 22,
        "minute": 10,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


check_strategy_data_task_config = {
    "func": check_strategy_data_task,
    "cron": {
        "id": "检查策略数据",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 22,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
