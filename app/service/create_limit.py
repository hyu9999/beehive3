from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.core.errors import PermissionDoesNotExist, CreateQuantityLimit, ParamsError
from app.crud.base import get_collection_by_config
from app.enums.common import 产品分类
from app.enums.equipment import 装备分类_3, 装备分类转换
from app.enums.portfolio import 组合状态
from app.models.user import User


async def 创建数量限制(conn: AsyncIOMotorClient, category: 产品分类, user: User, 装备分类: 装备分类_3 = None):
    if user.roles[0] == "超级用户":
        return True
    filters = {}
    if category == 产品分类.equipment:
        if 装备分类:
            filters = {"作者": user.username, "标识符": {"$regex": f"^{装备分类转换[装备分类]}.*"}, "状态": {"$nin": ["已删除"]}}
        else:
            raise ParamsError(message="参数错误，缺失参数")
    elif category == 产品分类.robot:
        filters = {"作者": user.username, "状态": {"$nin": ["已删除", "临时回测"]}}
    elif category == 产品分类.portfolio:
        filters = {
            "username": user.username,
            "status": 组合状态.running.value,
            "activity": {"$not": {"$exists": True, "$ne": None}},
        }
    exec("from app.enums.common import 中文产品分类")
    cn_category = eval(f'中文产品分类.{category}')
    cnt = await get_collection_by_config(conn, f"{cn_category}信息collection名").count_documents(filters)
    if category not in settings.num_limit[user.roles[0]].keys():
        raise PermissionDoesNotExist()
    if cnt >= settings.num_limit[user.roles[0]][category]:
        raise CreateQuantityLimit(message=f"创建{cn_category}数达到上限，最多只能创建{settings.num_limit[user.roles[0]][category]}个")
    return True
