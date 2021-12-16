from datetime import datetime
from typing import List

from stralib.models.robot import 机器人状态, 机器人可见模式, 减仓模式分类, 卖出筛选器分类, 买入筛选器分类, 保证持仓数量筛选器分类

from app.enums.robot import 机器人评级

robot_columns = [
    {"正式名称": "sid", "别名": ["标识符"], "类型": str, "描述": ""},
    {"正式名称": "name", "别名": ["名称"], "类型": str, "描述": ""},
    {"正式名称": "avatar", "别名": ["头像"], "类型": str, "描述": ""},
    {"正式名称": "bio", "别名": ["简介"], "类型": str, "描述": ""},
    {"正式名称": "homepage", "别名": ["主页地址"], "类型": str, "描述": ""},
    {"正式名称": "作者", "别名": ["author"], "类型": str, "描述": ""},
    {"正式名称": "状态", "别名": ["status"], "类型": 机器人状态, "描述": ""},
    {"正式名称": "创建时间", "别名": ["create_time"], "类型": datetime, "描述": ""},
    {"正式名称": "上线时间", "别名": ["online_time"], "类型": datetime, "描述": ""},
    {"正式名称": "下线时间", "别名": ["offline_time"], "类型": datetime, "描述": ""},
    {"正式名称": "回测开始时间", "别名": ["backtest_start_time"], "类型": datetime, "描述": ""},
    {"正式名称": "回测结束时间", "别名": ["backtest_end_time"], "类型": datetime, "描述": ""},
    {"正式名称": "标签", "别名": ["tag"], "类型": List[str], "描述": ""},
    {"正式名称": "可见模式", "别名": ["visible_mode"], "类型": 机器人可见模式, "描述": ""},
    {"正式名称": "评级", "别名": ["rating"], "类型": 机器人评级, "描述": ""},
    {"正式名称": "风控包标识符", "别名": ["risk_package_sid"], "类型": str, "描述": ""},
    {"正式名称": "择时装备列表", "别名": ["timing_sid_list"], "类型": List[str], "描述": ""},
    {"正式名称": "风控装备列表", "别名": ["risk_sid_list"], "类型": List[str], "描述": ""},
    {"正式名称": "选股装备列表", "别名": ["stock_sid_list"], "类型": List[str], "描述": ""},
    {"正式名称": "交易装备列表", "别名": ["trade_sid_list"], "类型": List[str], "描述": ""},
    {"正式名称": "减仓模式", "别名": ["reduce_mode"], "类型": List[减仓模式分类], "描述": ""},
    {"正式名称": "卖出筛选器", "别名": ["sold_filter_strategy_list"], "类型": List[卖出筛选器分类], "描述": ""},
    {"正式名称": "买入筛选器", "别名": ["buy_filter_strategy_list"], "类型": List[买入筛选器分类], "描述": ""},
    {"正式名称": "保证持仓数量筛选器", "别名": ["filter_buy_stock_symbol"], "类型": List[保证持仓数量筛选器分类], "描述": ""},
    {"正式名称": "分析了多少支股票", "别名": ["analysis_stock_num"], "类型": int, "描述": ""},
    {"正式名称": "管理了多少组合", "别名": ["manage_portfolio_num"], "类型": int, "描述": ""},
    {"正式名称": "累计管理资金", "别名": ["accumulate_management_funds"], "类型": float, "描述": ""},
    {"正式名称": "累计创造收益", "别名": ["accumulate_produce_income"], "类型": float, "描述": ""},
    {"正式名称": "运行天数", "别名": ["running_days"], "类型": int, "描述": ""},
    {"正式名称": "累计产生信号数", "别名": ["accumulate_generate_signals"], "类型": int, "描述": ""},
    {"正式名称": "累计服务人数", "别名": ["accumulate_serve_people"], "类型": int, "描述": ""},
    {"正式名称": "计算时间", "别名": ["computing_time"], "类型": datetime, "描述": ""},
    {"正式名称": "订阅人数", "别名": ["subscribers"], "类型": int, "描述": ""},
]
