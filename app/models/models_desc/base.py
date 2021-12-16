from app.models.models_desc.backtest_assess_robot import backtest_assess_robot_columns
from app.models.models_desc.backtest_assess_screens import backtest_assess_screens_columns
from app.models.models_desc.backtest_assess_timings import backtest_assess_timings_columns
from app.models.models_desc.backtest_indicator_robot import backtest_indicator_robot_columns
from app.models.models_desc.backtest_indicator_screens import backtest_indicator_screens_columns
from app.models.models_desc.backtest_indicator_timings import backtest_indicator_timings_columns
from app.models.models_desc.backtest_signal_robot import backtest_signal_robot_columns
from app.models.models_desc.backtest_signal_screens import backtest_signal_screens_columns
from app.models.models_desc.backtest_signal_timings import backtest_signal_timings_columns
from app.models.models_desc.equipment import equipment_columns
from app.models.models_desc.permission import permission_columns
from app.models.models_desc.real_indicator_robot import real_indicator_robot_columns
from app.models.models_desc.real_signal_robot import real_signal_robot_columns
from app.models.models_desc.real_signal_screens import real_signal_screens_columns
from app.models.models_desc.real_signal_timings import real_signal_timings_columns
from app.models.models_desc.robot import robot_columns
from app.models.models_desc.role import role_columns
from app.models.models_desc.stock import stock_columns
from app.models.models_desc.user import user_columns

collections = [
    {"正式名称": "users", "别名": ["用户"], "字段列表": user_columns, "描述": "用于存储用户基本数据"},
    {"正式名称": "robots", "别名": ["机器人"], "字段列表": robot_columns, "描述": "用于存储机器人基础数据"},
    {"正式名称": "equipment", "别名": ["装备"], "字段列表": equipment_columns, "描述": "用于存储装备基础数据"},
    {"正式名称": "permissions", "别名": ["角色权限"], "字段列表": permission_columns, "描述": "用于存储角色权限基础数据"},
    {"正式名称": "roles", "别名": ["角色"], "字段列表": role_columns, "描述": "用于存储角色基础数据"},
    {"正式名称": "stock", "别名": ["股票"], "字段列表": stock_columns, "描述": "用于存储股票基础数据"},
    {"正式名称": "backtest_assess_robot", "别名": ["机器人回测评级"], "字段列表": backtest_assess_robot_columns, "描述": "用于存储机器人回测评级基础数据"},
    {"正式名称": "backtest_assess_screens", "别名": ["选股装备回测评级"], "字段列表": backtest_assess_screens_columns, "描述": "用于存储选股装备回测评级基础数据"},
    {"正式名称": "backtest_assess_timings", "别名": ["择时装备回测评级"], "字段列表": backtest_assess_timings_columns, "描述": "用于存储择时装备回测评级基础数据"},
    {"正式名称": "backtest_signal_robot", "别名": ["机器人回测信号"], "字段列表": backtest_signal_robot_columns, "描述": "用于存储机器人回测信号基础数据"},
    {"正式名称": "backtest_signal_screens", "别名": ["选股装备回测信号"], "字段列表": backtest_signal_screens_columns, "描述": "用于存储选股装备回测信号基础数据"},
    {"正式名称": "backtest_signal_timings", "别名": ["择时装备回测信号"], "字段列表": backtest_signal_timings_columns, "描述": "用于存储择时装备回测信号基础数据"},
    {"正式名称": "backtest_indicator_robot", "别名": ["机器人回测指标"], "字段列表": backtest_indicator_robot_columns, "描述": "用于存储机器人回测指标基础数据"},
    {"正式名称": "backtest_indicator_screens", "别名": ["选股装备回测指标"], "字段列表": backtest_indicator_screens_columns, "描述": "用于存储选股装备回测指标基础数据"},
    {"正式名称": "backtest_indicator_timings", "别名": ["择时装备回测指标"], "字段列表": backtest_indicator_timings_columns, "描述": "用于存储择时装备回测指标基础数据"},
    {"正式名称": "real_signal_robot", "别名": ["机器人实盘信号"], "字段列表": real_signal_robot_columns, "描述": "用于存储机器人实盘信号基础数据"},
    {"正式名称": "real_signal_screens", "别名": ["选股装备实盘信号"], "字段列表": real_signal_screens_columns, "描述": "用于存储选股装备实盘信号基础数据"},
    {"正式名称": "real_signal_timings", "别名": ["择时装备实盘信号"], "字段列表": real_signal_timings_columns, "描述": "用于存储择时装备实盘信号基础数据"},
    {"正式名称": "real_indicator_robot", "别名": ["机器人实盘指标"], "字段列表": real_indicator_robot_columns, "描述": "用于存储择时机器人实盘指标基础数据"},
]



def to_json():
    """将所有的字段定义转换成能够粘贴到studio 3t的json文档"""
    j = []
    for dict_item in collections:
        for dict_item1 in dict_item["字段列表"]:
            for key in dict_item1:
                if key == "类型" and hasattr(dict_item1[key], "__name__"):
                    dict_item1[key] = dict_item1[key].__name__
                elif key == "类型" and hasattr(dict_item1[key], "__class__"):
                    dict_item1[key] = dict_item1[key].__class__.__name__
            j.append(dict_item1)
    return str(j)
