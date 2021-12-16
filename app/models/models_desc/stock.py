from datetime import datetime

from app.enums.stock import 股票市场Enum

stock_columns = [
    {"正式名称": "symbol", "别名": [], "类型": str, "描述": "股票代码"},
    {"正式名称": "exchange", "别名": [], "类型": 股票市场Enum, "描述": "股票市场"},
    {"正式名称": "symbol_name", "别名": [], "类型": str, "描述": "股票名称"},
    {"正式名称": "symbol_shortname", "别名": [], "类型": str, "描述": "股票简称"},
    {"正式名称": "industry", "别名": [], "类型": str, "描述": "行业"},
    {"正式名称": "update_time", "别名": [], "类型": datetime, "描述": "更新时间"},
]
