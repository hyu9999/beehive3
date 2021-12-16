from app.schedulers.disc.func import fill_disc_data

fill_disc_data_config = {
    "func": fill_disc_data,
    "cron": {
        "trigger": "cron",
        "id": "同步社区用户及其文章",
        "day_of_week": "0-6",
        "hour": 1,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}