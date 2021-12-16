from app.schedulers.portfolio.func import update_portfolio_profit_rank_data

update_portfolio_profit_rank_data_config = {
    "func": update_portfolio_profit_rank_data,
    "cron": {
        "id": "更新组合总收益排行数据",
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
