from typing import List

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_tags_collection, get_robots_collection, get_equipment_collection
from app.enums.equipment import 装备状态
from app.enums.robot import 机器人状态
from app.enums.tag import TagType
from app.models.rwmodel import PyObjectId
from app.models.tag import Tag
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.tag import TagInUpdate


async def 获取标签列表(conn: AsyncIOMotorClient, query: dict, status: str = None, 评级: list = None) -> List[Tag]:
    if not status:
        tags_cursor = get_tags_collection(conn).find(query)
        return [Tag(**tag) async for tag in tags_cursor]
    else:
        if query["category"] == TagType.机器人 and status in 机器人状态.__members__:
            db_query = {"状态": status, "评级": {"$in": 评级}, "可见模式": "完全公开"}
            robot_cursor = get_robots_collection(conn).find(db_query)
            robot_tags = []
            async for robot in robot_cursor:
                robot_tags.extend(robot["标签"])
            return [Tag(name=tag, category=TagType.机器人) for tag in set(robot_tags)]
        elif query["category"] == TagType.装备 and status in 装备状态.__members__:
            db_query = {"状态": status, "评级": {"$in": 评级}, "可见模式": "完全公开", "分类": {"$in": ["选股", "择时", "风控包"]}}
            equipment_cursor = get_equipment_collection(conn).find(db_query)
            equipment_tags = []
            async for equipment in equipment_cursor:
                equipment_tags.extend(equipment["标签"])
            return [Tag(name=tag, category=TagType.装备) for tag in set(equipment_tags)]


async def 新建标签(conn: AsyncIOMotorClient, tags: List[str], tag_type: TagType):
    for tag in tags:
        if not await get_tags_collection(conn).find_one({"name": tag, "category": tag_type}):
            await get_tags_collection(conn).insert_one({"name": tag, "category": tag_type})


async def 删除标签(conn: AsyncIOMotorClient, id: PyObjectId) -> ResultInResponse:
    result = await get_tags_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def 全量更新标签(conn: AsyncIOMotorClient, id: PyObjectId, tag: Tag) -> UpdateResult:
    result = await get_tags_collection(conn).update_one({"_id": id}, {"$set": tag.dict()})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)


async def 部分更新标签(conn: AsyncIOMotorClient, id: PyObjectId, tag: TagInUpdate) -> UpdateResult:
    result = await get_tags_collection(conn).update_one({"_id": id}, {"$set": tag.dict(exclude_defaults=True)})
    return UpdateResult(matched_count=result.matched_count, modified_count=result.modified_count)
