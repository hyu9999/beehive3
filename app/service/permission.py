from app.core.errors import RobotNoPermissionToUse
from app.dec import permission_check_decor
from app.schema.user import User


@permission_check_decor
def check_robot_permission(sid: str, user: User):
    """检查机器人使用权限"""
    if "厂商用户" in user.roles and sid[:14] not in user.client.robot:
        raise RobotNoPermissionToUse(message=f"{user.nickname}没有该机器人[{sid}]的使用权限")


@permission_check_decor
def check_equipment_permission(sid: str, user: User):
    """检查装备使用权限"""
    if "厂商用户" in user.roles and sid not in user.client.equipment:
        raise RobotNoPermissionToUse(message=f"{user.nickname}没有该装备[{sid}]的使用权限")
