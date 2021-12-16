from app.schedulers.risk.func import risk_detection_with_condition_task, risk_detection_task, preload_robot_data

risk_detection_with_condition_config = {
    "func": risk_detection_with_condition_task,
    "cron": {
        "id": "风险检测_检查装备状态",
        "trigger": "cron",
        "day_of_week": "0-6",
        "hour": 23,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
risk_detection_config = {
    "func": risk_detection_task,
    "cron": {
        "id": "风险检测",
        "trigger": "cron",
        "day_of_week": "0-6",
        "hour": 21,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

preload_robot_data_config = {
    "func": preload_robot_data,
    "cron": {
        "trigger": "cron",
        "day_of_week": "0-6",
        "hour": 0,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
