from app.schedulers.cn_collection.func import increment_update_cn_collection_data, added_missing_real_collection_data

increment_update_cn_collection_data_config = {
    "func": increment_update_cn_collection_data,
    "cron": {
        "trigger": "cron",
        "id": "更新中文表",
        "day_of_week": "0-6",
        "hour": "19-23",
        "minute": "*/20",
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


added_missing_real_collection_data_config = {
    "func": added_missing_real_collection_data,
    "cron": {
        "trigger": "cron",
        "id": "补充实盘缺失数据",
        "day_of_week": "0-6",
        "hour": 1,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
