from app.schedulers.wechat.func import sync_wechat_avatar_task

sync_wechat_avatar_config = {
    "func": sync_wechat_avatar_task,
    "cron": {
        "id": "每日同步微信头像",
        "trigger": "cron",
        "day_of_week": "0-6",
        "hour": 3,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}