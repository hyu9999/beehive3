from typing import List, Union

from fastapi import APIRouter, Query, Security, Depends, Body, Path
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.jwt import get_current_user_authorizer
from app.crud.tag import 获取标签列表, 新建标签, 删除标签, 全量更新标签, 部分更新标签
from app.db.mongodb import get_database
from app.enums.equipment import 装备状态, 装备评级
from app.enums.robot import 机器人状态, 机器人评级
from app.enums.tag import TagType
from app.models.rwmodel import PyObjectId
from app.models.tag import Tag
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.tag import TagInUpdate

router = APIRouter()


@router.get("", response_model=List[Tag], description="查询标签列表")
async def list_view(
    分类: TagType = Query(None),
    状态: Union[机器人状态, 装备状态] = Query("已上线"),
    评级: List[Union[机器人评级, 装备评级]] = Query(["A", "B", "C"]),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["标签:查看"]),
):
    query = {}
    if 分类:
        query["category"] = 分类
    return await 获取标签列表(db, query, 状态, 评级)


@router.post("", description="创建标签")
async def create_view(
    tags: List[str] = Query(..., description="标签列表"),
    category: TagType = Query(..., description="标签类型"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["标签:创建"]),
):
    await 新建标签(db, tags, category)


@router.delete("/{id}", response_model=ResultInResponse, description="删除标签")
async def delete_view(
    id: PyObjectId = Path(...), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["标签:删除"]),
):
    return await 删除标签(db, id)


@router.put("/{id}", response_model=UpdateResult, description="全量更新标签")
async def put_view(
    id: PyObjectId = Path(...),
    tag: Tag = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["标签:修改"]),
):
    return await 全量更新标签(db, id, tag)


@router.patch("/{id}", response_model=UpdateResult, description="部分更新标签")
async def pacth_view(
    id: PyObjectId = Path(...),
    tag: TagInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["标签:修改"]),
):
    return await 部分更新标签(db, id, tag)
