from app.schedulers.order.func import close_order_task, place_order_task, check_order_task, check_order_bills_task

close_order_config = {
    "func": close_order_task,
    "cron": {
        "trigger": "cron",
        "id": "每日收盘重置旧的风险",
        "day_of_week": "0-4",
        "hour": 15,
        "minute": 5,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
place_order_config = {
    "func": place_order_task,
    "cron": {
        "id": "每日自动委托下单-上午",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 9,
        "minute": 30,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

check_order_config = {
    "func": check_order_task,
    "cron": {
        "id": "每日委托订单实时检测",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 9,
        "minute": 30,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

check_order_bills_config = {
    "func": check_order_bills_task,
    "cron": {
        "id": "每日核对股票订单",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 23,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
