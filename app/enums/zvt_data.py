from enum import Enum


class ZvtDataLogState(str, Enum):
    """ZVT数据状态"""
    completed = "已完成"
    unfinished = "未完成"
