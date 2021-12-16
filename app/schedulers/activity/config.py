from app.schedulers.activity.func import activity_online_task, activity_finished_task


activity_online_task_config = {
    "func": activity_online_task,
    "cron": {
        "trigger": "cron",
        "id": "活动上线",
        "day_of_week": "0-6",
        "hour": 0,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
activity_finished_task_config = {
    "func": activity_finished_task,
    "cron": {
        "id": "活动结算",
        "trigger": "cron",
        "day_of_week": "0-6",
        "hour": 16,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
