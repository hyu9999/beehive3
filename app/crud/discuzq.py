from datetime import datetime
from typing import List

from app.core.discuzq import Discuzq
from app.core.discuzqlib.exception import DiscuzqError
from app.core.errors import DiscuzqCustomError
from app.dec import disc_switch_decor


async def get_thread_reply_ids(thread_id, skip, limit):
    """
    根据主题id拿到一级回复的id
    """
    res = await Discuzq.admin().get_post_from_thread(thread_id, skip, limit)
    return {
        "count": len(res["data"]),
        "data": [p["id"] for p in res["data"]],
        "skip": skip,
        "limit": limit,
    }


async def get_thread_replies(username: str, thread_id: int, post_ids: List[str]):
    """
    根据post id拿到详细内容
    """
    try:
        res = await Discuzq.client(username).get_post_from_thread(thread_id, 0, 100000)
        target_posts = [p for p in res["data"] if p["id"] in post_ids]
        if len(target_posts) == 0:
            return []

        users_involved = {
            u["attributes"]["id"]: u["attributes"]["username"]
            for u in res["included"]
            if u["type"] == "users"
        }
        realname_involved = {
            u["id"]: u["attributes"]["signature"]
            for u in res["included"]
            if u["type"] == "users"
        }
        return [
            {
                "post_number": p["id"],
                "display_username": realname_involved[
                    p["relationships"]["user"]["data"]["id"]
                ],
                "cooked": p["attributes"]["content"],
                "created_at": p["attributes"]["createdAt"],
                "like_count": p["attributes"]["likeCount"],
                "is_self": users_involved[int(p["relationships"]["user"]["data"]["id"])]
                == username,
                "is_liked": p["attributes"]["isLiked"],
            }
            for p in target_posts
        ]
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"查询回复失败，{e}")


async def get_post_replies(post_id, skip, limit):
    """
    根据post id拿到楼中楼回复的详细内容
    """
    try:
        res = await Discuzq.admin().get_post_replies(post_id, skip, limit)
        target_replies = res["data"]
        if len(target_replies) == 0:
            return []
        users_involved = {
            u["attributes"]["id"]: u["attributes"]["username"]
            for u in res["included"]
            if u["type"] == "users"
        }
        return [
            {
                "post_number": p["id"],
                "display_username": users_involved[
                    int(p["relationships"]["user"]["data"]["id"])
                ],
                "cooked": p["attributes"]["content"],
                "created_at": p["attributes"]["createdAt"],
                "like_count": p["attributes"]["likeCount"],
            }
            for p in target_replies
        ]
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"查询楼中楼回复失败，{e}")


async def like_post(username, pid):
    """
    点赞帖子
    """
    try:
        await Discuzq.client(username).like_post(pid)
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"点赞失败，{e}")


async def unlike_post(username, pid):
    """
    取消点赞帖子
    """
    try:
        await Discuzq.client(username).unlike_post(pid)
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"取消点赞失败，{e}")


async def create_post(username, post_id, raw, reply_id=0):
    """
    创建帖子回复，或者楼中楼回复
    """
    try:
        res = await Discuzq.client(username).create_post(raw, post_id, reply_id)
        return {
            "display_username": username,
            "cooked": raw,
            "created_at": datetime.utcnow().isoformat().split(".")[0] + "+08:00",
            "like_count": 0,
            "is_liked": False,
            "is_self": True,
            "post_id": res["id"],
        }
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"创建帖子失败，{e}")


async def create_disc_user(username=None, password=None):
    """创建社区用户"""
    try:
        ret_data = await Discuzq.admin().register(username, password)
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"创建社区用户失败，{e}")
    return ret_data


async def update_user_signature(user_id, signature):
    try:
        ret_data = await Discuzq.admin().update_user_signature(user_id, signature)
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"更新帖区用户失败，{e}")
    return ret_data


async def get_disc_user(username):
    """查询社区用户"""
    try:
        ret_data = await Discuzq.admin().get_user(username)
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"创建社区用户失败，{e}")
    return ret_data


@disc_switch_decor
async def get_or_create_disc_user(username):
    """
    查询社区用户如果没查询到则创建
    Parameters
    ----------
    username

    Returns
    -------

    """
    try:
        discuz_id = await Discuzq.admin().getsert_user(
            username, "{}@discuzQcom".format(username)
        )
        return discuz_id
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"创建社区用户失败，{e}")


async def delete_disc_user(user_id):
    """删除社区用户"""
    try:
        ret_data = await Discuzq.admin().delete_user(user_id)
        return ret_data
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"删除社区用户失败，{e}")


async def delete_post(username, post_id):
    """删除帖子"""
    try:
        ret_data = await Discuzq.client(username).delete_post(post_id)
        return ret_data
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"删除帖子失败，{e}")


async def update_post(username, post_id, content, **kwargs):
    """更新帖子"""
    try:
        ret_data = await Discuzq.client(username).update_post(
            post_id, content=content, **kwargs
        )
        return ret_data
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"更新帖子失败，{e}")


@disc_switch_decor
async def create_thread(username, title, raw, category):
    """发布文章"""
    try:
        ret_data = await Discuzq.client(username).create_thread(title, raw, category)
        return ret_data
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"创建主题失败，{e}")


async def delete_thread(username, thread_id):
    """删除文章"""
    try:
        ret_data = await Discuzq.client(username).delete_thread(thread_id)
        return ret_data
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"删除主题失败，{e}")


async def update_thread_title(username, thread_id, title):
    """更新文章标题"""
    try:
        ret_data = await Discuzq.client(username).update_thread(thread_id, title=title)
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"更新主题标题失败，{e}")


async def get_thread(thread_id):
    """获取文章信息"""
    try:
        thread = await Discuzq.admin().get_thread(thread_id)
        return thread
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"获取主题失败，{e}")


async def get_user_created_threads(username, skip, limit):
    """获取用户的文章列表"""
    try:
        threads = await Discuzq.client(username).user_created_threads(
            username, skip, limit
        )
        return threads
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"获取主题失败，{e}")


async def get_user_marked_threads(username, skip=0, limit=10):
    """关注文章列表"""
    try:
        threads = await Discuzq.client(username).my_bookmarked_threads(skip, limit)
        return threads
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"查询失败，{e}")


async def mark_thread(username, thread_id):
    """关注文章"""
    try:
        ret_data = await Discuzq.client(username).bookmark_thread(thread_id)
        return ret_data
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"关注文章失败，{e}")


async def unmark_thread(username, thread_id):
    """取消关注文章"""
    try:
        ret_data = await Discuzq.client(username).unmark_thread(thread_id)
    except DiscuzqError as e:
        raise DiscuzqCustomError(message=f"取消关注文章失败，{e}")
