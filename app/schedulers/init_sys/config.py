from datetime import datetime, timedelta

from app.schedulers.init_sys.func import (
    check_order_onstart_task,
    place_order_onstart_task, update_strategy_calculate_datetime_task,
)
from app.schedulers.portfolio.func import update_portfolio_profit_rank_data

place_order_onstart_config = {
    "func": place_order_onstart_task,
    "cron": {
        "id": "初始化系统必需数据-委托订单下单",
        "trigger": "cron",
        "day_of_week": "0-4",
        "next_run_time": datetime.now() + timedelta(seconds=2),
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

check_order_onstart_config = {
    "func": check_order_onstart_task,
    "cron": {
        "id": "初始化系统必需数据-每日委托订单实时检测",
        "trigger": "cron",
        "day_of_week": "0-4",
        "next_run_time": datetime.now() + timedelta(seconds=5),
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

update_portfolio_profit_rank_data_onstart_config = {
    "func": update_portfolio_profit_rank_data,
    "cron": {
        "id": "初始化系统必需数据-更新组合总收益排行数据",
        "trigger": "cron",
        "day_of_week": "0-4",
        "next_run_time": datetime.now() + timedelta(seconds=5),
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

update_strategy_calculate_datetime_onstart_config = {
    "func": update_strategy_calculate_datetime_task,
    "cron": {
        "trigger": "cron",
        "id": "初始化系统必需数据-更新策略计算时间",
        "day_of_week": "0-4",
        "next_run_time": datetime.now() + timedelta(seconds=5),
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}