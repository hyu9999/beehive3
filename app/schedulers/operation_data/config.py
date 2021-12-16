from app.schedulers.init_sys.func import update_strategy_calculate_datetime_task
from app.schedulers.operation_data.func import update_strategy_calculate_datetime, update_operation_data

update_operation_data_config = {
    "func": update_operation_data,
    "cron": {
        "trigger": "cron",
        "id": "更新运行机器人-装备数据",
        "day_of_week": "0-6",
        "hour": "21-23",
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
update_strategy_calculate_datetime_config = {
    "func": update_strategy_calculate_datetime_task,
    "cron": {
        "trigger": "cron",
        "id": "更新策略计算时间",
        "day_of_week": "0-4",
        "hour": 19,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
