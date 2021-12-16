from typing import List
from datetime import datetime

from app.enums.equipment import 装备状态, 装备信号传入方式, 装备可见模式, 装备评级, 装备分类_3

equipment_columns = [
    {"正式名称": "sid", "别名": ["标识符"], "类型": str, "描述": ""},
    {"正式名称": "name", "别名": ["名称"], "类型": str, "描述": ""},
    {"正式名称": "bio", "别名": ["简介"], "类型": str, "描述": ""},
    {"正式名称": "homepage", "别名": ["主页地址"], "类型": str, "描述": ""},
    {"正式名称": "作者", "别名": ["author"], "类型": str, "描述": ""},
    {"正式名称": "分类", "别名": [], "类型": 装备分类_3, "描述": ""},
    {"正式名称": "状态", "别名": ["status"], "类型": 装备状态, "描述": ""},
    {"正式名称": "标签", "别名": ["tag"], "类型": List[str], "描述": ""},
    {"正式名称": "英文名", "别名": ["english_name"], "类型": str, "描述": ""},
    {"正式名称": "创建时间", "别名": ["create_time"], "类型": datetime, "描述": ""},
    {"正式名称": "上线时间", "别名": ["online_time"], "类型": datetime, "描述": ""},
    {"正式名称": "下线时间", "别名": ["offline_time"], "类型": datetime, "描述": ""},
    {"正式名称": "信号传入方式", "别名": [], "类型": 装备信号传入方式, "描述": ""},
    {"正式名称": "可见模式", "别名": [], "类型": 装备可见模式, "描述": ""},
    {"正式名称": "评级", "别名": ["rating"], "类型": 装备评级, "描述": ""},
    {"正式名称": "计算时间", "别名": ["computing_time"], "类型": datetime, "描述": ""},
    {"正式名称": "运行天数", "别名": ["running_days"], "类型": int, "描述": ""},
    {"正式名称": "累计服务人数", "别名": ["accumulate_serve_people"], "类型": int, "描述": ""},
    {"正式名称": "累计产生信号数", "别名": ["accumulate_generate_signals"], "类型": int, "描述": ""},
    {"正式名称": "订阅人数", "别名": ["subscribers"], "类型": int, "描述": ""},
    {"正式名称": "源代码", "别名": [], "类型": str, "描述": ""},
    {"正式名称": "指数列表", "别名": ["index_list"], "类型": List[str], "描述": ""},
    {"正式名称": "装备列表", "别名": ["equipment_list"], "类型": List[str], "描述": ""},
]
