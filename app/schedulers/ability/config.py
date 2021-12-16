from .func import (
    calculate_manual_import_portfolio_ability_task,
    calculate_simulated_trading_portfolio_ability_task,
)

calculate_simulated_trading_portfolio_ability_config = {
    "func": calculate_simulated_trading_portfolio_ability_task,
    "cron": {
        "trigger": "cron",
        "id": "模拟交易组合战斗力评估",
        "day_of_week": "0-4",
        "hour": 16,
        "minute": 20,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


calculate_manual_import_portfolio_ability_config = {
    "func": calculate_manual_import_portfolio_ability_task,
    "cron": {
        "trigger": "cron",
        "id": "手动调仓组合战斗力评估",
        "day_of_week": "0-4",
        "hour": 23,
        "minute": 00,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 3600,
    },
}
