import asyncio
from functools import wraps
from typing import List

import aiohttp

from app.core.discuzqlib.exception import DiscuzqError


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if args[0].access_token == "":
            await args[0].login()
        return await func(*args, **kwargs)

    return wrapper


def renew_client_token(func):
    """
    装饰器，如果发现401，那么就进行登陆或者access
    token的renew操作
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DiscuzqError:
            if args[0].access_token != "":
                return await args[0].renew_token()
            else:
                await args[0].login()
                return await func(*args, **kwargs)

    return wrapper


class DiscuzqClient:
    def __init__(self, url, username, password):
        self.max_len = 15  # 社区用户长度最大为15
        self.url = url
        self.login_uri = "{}/{}".format(self.url, "api/login")
        self.register_uri = "{}/{}".format(self.url, "api/register")
        self.username = username[:self.max_len]
        self.password = password
        self.access_token = ""
        self.refresh_token = ""
        self._sess = aiohttp.ClientSession()

    @renew_client_token
    async def _patch_req(self, uri, payload):
        async with self._sess.patch(uri, json=payload) as resp:
            res = await resp.json()
            if "errors" in res:
                raise DiscuzqError(res["errors"])
            else:
                return res

    @renew_client_token
    async def _get_req(self, uri, skip=None, limit=None):
        if skip:
            uri = "{}&page[offset]={}".format(uri, skip)
        if limit:
            uri = "{}&page[limit]={}".format(uri, limit)

        async with self._sess.get(uri) as resp:
            res = await resp.json()
            if "errors" in res:
                raise DiscuzqError(res["errors"])
            else:
                return res

    @renew_client_token
    async def _delete_req(self, uri, payload):
        async with self._sess.delete(uri, json=payload) as resp:
            res = await resp.json()
            if "errors" in res:
                raise DiscuzqError(res["errors"])
            else:
                return res

    @renew_client_token
    async def _post_req(self, uri, payload):
        async with self._sess.post(uri, json=payload) as resp:
            res = await resp.json()
            if "errors" in res:
                raise DiscuzqError(res["errors"])
            else:
                return res

    async def renew_token(self):
        """
        访问API进行accesss token的renew操作
        """
        payload = {
            "data": {
                "attributes": {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                }
            }
        }
        self._sess = aiohttp.ClientSession(headers={})
        async with self._sess.post(
            "{}/api/refresh-token".format(self.url), json=payload
        ) as resp:
            res = await resp.json()
            if "errors" in res:
                raise DiscuzqError(res["errors"])
            else:
                self.access_token = res["data"]["attributes"]["access_token"]
                self.refresh_token = res["data"]["attributes"]["refresh_token"]
                self._sess = aiohttp.ClientSession(
                    headers={"Authorization": "Bearer {}".format(self.access_token)}
                )

    async def login(self):
        """
        登陆
        """
        payload = {
            "data": {
                "attributes": {
                    "username": self.username,
                    "password": self.password
                    if self.password
                    else "{}@discuzQcom".format(self.username),
                }
            }
        }
        async with self._sess.post(self.login_uri, json=payload) as resp:
            res = await resp.json()
            if "errors" in res:
                raise DiscuzqError(res["errors"])
            else:
                self.access_token = res["data"]["attributes"]["access_token"]
                self.refresh_token = res["data"]["attributes"]["refresh_token"]
                self._sess = aiohttp.ClientSession(
                    headers={"Authorization": "Bearer {}".format(self.access_token)}
                )

    async def register(self, username: str, password: str):
        """
        进行新用户的注册
        Args:
            username ([str]): [用户名]
            password ([str]): [密码]

        """
        payload = {
            "data": {
                "type": "users",
                "attributes": {
                    "username": username[:self.max_len],
                    "password": password,
                },
            }
        }
        async with self._sess.post(self.register_uri, json=payload) as resp:
            res = await resp.json()
            if "errors" in res:
                raise DiscuzqError(res["errors"])
            else:
                self.access_token = res["data"]["attributes"]["access_token"]
                self.refresh_token = res["data"]["attributes"]["refresh_token"]
                return {"id": int(res["data"]["id"])}

    async def getsert_user(self, username: str, password: str):
        """
            获取用户，如果用户不存在，就新创建用户
        Args:
            username ([str]): [用户名]
            password ([str]): [密码]

        """
        user = await self.get_user(username[:self.max_len])
        if user:
            return user["id"]
        else:
            user = await self.register(username[:self.max_len], password)
            return user["id"]

    async def create_category(self, name: str, description: str):
        """
        创建帖子的类别

        Args:
            name (str): [分类名]
            description (str): [分类的描述]
        """
        payload = {
            "data": [
                {
                    "type": "categories",
                    "attributes": {"name": name, "description": description},
                }
            ]
        }
        res = await self._post_req(
            "{}/{}".format(self.url, "api/categories/batch"), payload
        )
        return res["data"][0]["attributes"]

    async def get_categories(self):
        """
        查询帖子分类
        """
        res = await self._get_req("{}/{}".format(self.url, "api/categories"))
        return {"data": [d["attributes"] for d in res["data"]]}

    async def delete_category(self, category_id: str):
        """
        删除帖子分类
        """
        res = await self._delete_req(
            "{}/{}/{}".format(self.url, "api/categories/batch", category_id), {}
        )
        return res

    @login_required
    async def create_thread(self, title: str, content: str, category_id: int):
        """
        创建主题
        """
        payload = {
            "data": {
                "type": "threads",
                "relationships": {
                    "category": {"data": {"type": "categories", "id": category_id}}
                },
                "attributes": {
                    "content": content,
                    "title": title,
                    "type": "1",
                    "is_draft": 0,
                    "is_old_draft": 0,
                },
            }
        }
        res = await self._post_req(
            "{}/{}".format(self.url, "api/threads"), payload=payload
        )
        return res["data"]["attributes"]

    @login_required
    async def delete_thread(self, thread_id: str):
        """
        删除主题
        """
        res = await self._delete_req(
            "{}/{}/{}".format(self.url, "api/threads/batch", thread_id), payload={}
        )
        return res["data"][0]["attributes"]

    @login_required
    async def get_thread(self, thread_id):
        """
        获得主题
        """
        res = await self._get_req("{}/{}/{}".format(self.url, "api/threads", thread_id))
        return res and res["data"] and res["data"]["attributes"] or res

    @login_required
    async def get_post_from_thread(self, thread_id, skip, limit):
        """
        获得主题一级评论
        """
        res = await self._get_req(
            "{}/{}{}&filter[isComment]=no&include=user".format(
                self.url, "api/posts?filter[thread]=", thread_id
            ),
            skip,
            limit,
        )
        return res

    @login_required
    async def update_thread(self, thread_id, **d):
        """
        更新主题
        """
        payload = {"data": {"type": "threads", "attributes": {**d}}}
        res = await self._patch_req(
            "{}/{}/{}".format(self.url, "api/threads", thread_id), payload=payload
        )
        return res["data"]["attributes"]

    @login_required
    async def create_post(self, content, thread_id, reply_id=0):
        """
        创建回复，如果reply_id有值，则为楼中楼
        """
        payload = {
            "data": {
                "type": "posts",
                "attributes": {"content": content},
                "relationships": {
                    "thread": {"data": {"type": "threads", "id": thread_id}}
                },
            }
        }
        if reply_id != 0:
            payload["data"]["attributes"]["replyId"] = reply_id
            payload["data"]["attributes"]["isComment"] = True
        res = await self._post_req(
            "{}/{}".format(self.url, "api/posts"), payload=payload
        )
        return res["data"]["attributes"]

    @login_required
    async def like_post(self, post_id):
        """
        点赞帖子或主题
        """
        return await self.update_post(post_id, isLiked=1)

    @login_required
    async def unlike_post(self, post_id):
        """
        取消点赞
        """
        return await self.update_post(post_id, isLiked=0)

    @login_required
    async def unmark_thread(self, thread_id):
        """
        取消收藏主题
        """
        return await self.update_thread(thread_id, isFavorite=False)

    @login_required
    async def bookmark_thread(self, thread_id):
        """
        收藏主题
        """
        return await self.update_thread(thread_id, isFavorite=True)

    @login_required
    async def delete_post(self, pid):
        """
        删除帖子
        """
        res = await self._delete_req(
            "{}/{}/{}".format(self.url, "api/posts/batch", pid), payload={}
        )
        return res["data"][0]["attributes"]

    @login_required
    async def update_user_signature(self, user_id, signature):
        payload = {"data": {"attributes": {"signature": signature}}}
        res = await self._patch_req(
            "{}/{}/{}".format(self.url, "api/users", user_id), payload=payload
        )
        return res

    @login_required
    async def update_post_content(self, pid, content):
        """
        更新帖子内容
        """
        return await self.update_post(pid, content=content)

    @login_required
    async def update_post(self, pid, **d):
        """
        更新帖子
        """
        payload = {"data": {"type": "posts", "attributes": {**d}}}
        res = await self._patch_req(
            "{}/{}/{}".format(self.url, "api/posts", pid), payload=payload
        )
        return res and (res["data"]["attributes"] if "data" in res else res) or res

    async def get_post_replies(self, rid, skip, limit):
        """
        获得楼中楼回复
        """
        res = await self._get_req(
            "{}/{}{}&include=user".format(self.url, "api/posts?filter[reply]=", rid),
            skip,
            limit,
        )
        return res

    async def get_user(self, username):
        """
        获得用户
        """
        res = await self._get_req(
            "{}/{}{}".format(self.url, "api/users?filter[username]=", username[:self.max_len])
        )
        return res["data"] and res["data"][0]["attributes"] or {}

    async def delete_user(self, id):
        """
        删除用户
        """
        payload = {"data": {"attributes": {"id": [id]}}}
        res = await self._delete_req(
            "{}/{}".format(self.url, "api/users"), payload=payload
        )
        return res

    @login_required
    async def my_bookmarked_threads(self, skip, limit):
        """
        我收藏的主题
        """
        res = await self._get_req("{}/{}".format(self.url, "api/favorites"))
        if "data" in res:
            res["data"] = res["data"][skip : skip + limit]
        return res

    @login_required
    async def my_like_posts(self, skip, limit):
        """
        我点赞的主题
        """
        res = await self._get_req("{}/{}".format(self.url, "api/likes"))
        if "data" in res:
            res["data"] = res["data"][skip : skip + limit]
        return res

    async def user_created_threads(self, username, skip, limit):
        """
        获得用户创建的主题
        """
        res = await self._get_req(
            "{}/{}{}".format(self.url, "api/threads?filter[username]=", username[:self.max_len]),
            skip,
            limit,
        )
        return [t["attributes"] for t in res["data"]]
