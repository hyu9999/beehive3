from datetime import datetime, timedelta

from .func import (
    liquidation_fund_asset_task,
    save_manual_import_portfolio_time_series_data_task,
    save_simulated_trading_portfolio_time_series_data_task,
    sync_time_series_data_task,
    save_manual_import_portfolio_time_series_data_task2
)

save_simulated_trading_portfolio_time_series_data_config = {
    "func": save_simulated_trading_portfolio_time_series_data_task,
    "cron": {
        "trigger": "cron",
        "id": "保存模拟交易组合资金账户时点数据(持仓时点数据和资产时点数据)",
        "day_of_week": "0-4",
        "hour": 16,
        "minute": 10,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


save_manual_import_portfolio_time_series_data_config = {
    "func": save_manual_import_portfolio_time_series_data_task,
    "cron": {
        "trigger": "cron",
        "id": "保存手动调仓组合资金账户时点数据(持仓时点数据和资产时点数据) - 1",
        "day_of_week": "0-4",
        "hour": 21,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


save_manual_import_portfolio_time_series_data_config2 = {
    "func": save_manual_import_portfolio_time_series_data_task2,
    "cron": {
        "trigger": "cron",
        "id": "保存手动调仓组合资金账户时点数据(持仓时点数据和资产时点数据) - 2",
        "day_of_week": "0-4",
        "hour": 22,
        "minute": 15,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


liquidation_fund_asset_config = {
    "func": liquidation_fund_asset_task,
    "cron": {
        "trigger": "cron",
        "id": "清算手动导入资金账户资产数据",
        "day_of_week": "0-4",
        "hour": 15,
        "minute": 5,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

sync_time_series_data_config = {
    "func": sync_time_series_data_task,
    "cron": {
        "id": "同步全部历史时点数据",
        "trigger": "cron",
        "day_of_week": "0-4",
        "next_run_time": datetime.now() + timedelta(seconds=10),
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
