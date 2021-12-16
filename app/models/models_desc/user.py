from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr

from app.models.equipment import 装备inDB
from app.models.robot import Robot

user_columns = [
    {"正式名称": "username", "别名": [], "类型": str, "描述": "用户名"},
    {"正式名称": "email", "别名": [], "类型": EmailStr, "描述": "邮箱"},
    {"正式名称": "bio", "别名": [], "类型": Optional[str], "描述": "介绍"},
    {"正式名称": "image", "别名": [], "类型": str, "描述": "头像"},
    {"正式名称": "roles", "别名": [], "类型": Optional[List[str]], "描述": "角色"},
    {"正式名称": "mobile", "别名": [], "类型": str, "描述": "手机"},
    {"正式名称": "equipment", "别名": [], "类型": List[装备inDB], "描述": "订阅的装备"},
    {"正式名称": "robot", "别名": [], "类型": List[Robot], "描述": "订阅的机器人"},
    {"正式名称": "created_at", "别名": ["createdAt"], "类型": datetime, "描述": "创建时间"},
    {"正式名称": "updated_at", "别名": ["updatedAt"], "类型": datetime, "描述": "更新时间"},
    {"正式名称": "salt", "别名": [], "类型": str, "描述": "盐值"},
    {"正式名称": "hashed_password", "别名": [], "类型": str, "描述": "哈希化的密码"},
]
