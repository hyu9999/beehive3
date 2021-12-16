from typing import List

from fastapi import APIRouter,  Security, Body, Path, Query
from starlette.status import HTTP_201_CREATED
from app.core.jwt import get_current_user_authorizer
from app.crud.discuzq import *
from app.enums.disc import 社区文章动作
from app.schema.common import ResultInResponse

router = APIRouter()


# =============================topic
@router.get("/article/{article_id}/stream", description="查询主题的帖子id列表")
async def get_article_stream_view(
        article_id: int = Path(...),
        skip: int = Query(0, ge=0),
        limit: int = Query(20, gt=0, description="限制返回的条数"),
        user=Security(get_current_user_authorizer(), scopes=["文章:查看"]),
):
    return await get_thread_reply_ids(article_id, skip, limit)


@router.get("/article/{article_id}/{username}/posts", description="查询主题评论")
async def get_topic_posts_view(
        article_id: int = Path(...),
        username: str = "",
        post_ids: List[str] = Query([]),
        user=Security(get_current_user_authorizer(), scopes=["文章:查看"]),
):
    return await get_thread_replies(username, article_id, post_ids)


@router.get("/post/{post_id}/replies", description="查询帖子回复")
async def get_post_replies_view(
        post_id: int = Path(...),
        skip: int = Query(0, ge=0),
        limit: int = Query(20, gt=0, description="限制返回的条数"),
        user=Security(get_current_user_authorizer(), scopes=["文章:查看"]),
):
    return await get_post_replies(post_id, skip, limit)


@router.post("/article/{article_id}/{username}/actions/{action_name}", description="查询帖子")
async def topic_action_view(
        article_id: int = Path(None),
        username: str = "",
        action_name: 社区文章动作 = Path(...), data: dict = Body(None),
        user=Security(get_current_user_authorizer(), scopes=["文章:查看"]),
):
    if action_name == 社区文章动作.like:
        await like_post(username, article_id)
    elif action_name == 社区文章动作.unlike:
        await unlike_post(username, article_id)
    else:
        return ResultInResponse(result="failure")
    return ResultInResponse()


@router.post("/post/{username}", status_code=HTTP_201_CREATED, description="创建帖子")
async def create_post_view(
        post=Body(...),
        username: str = "",
        user=Security(get_current_user_authorizer(), scopes=["文章:创建"]),
):
    return await create_post(username, **post)

