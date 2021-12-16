users = []
category = {"data": []}
threads = []


class MockUpDiscClient:
    async def login(self):
        pass

    async def register(self, username: str, password: str):
        u = {"id": len(users) + 1, "username": username}
        users.append(u)
        return u

    async def get_user(self, username):
        for u in users:
            if u["username"] == username:
                return u
        return {}

    async def delete_user(self, id):
        global users
        users = [u for u in users if u["id"] != id]
        return users

    async def getsert_user(self, username: str, password: str):
        u = await self.get_user(username)
        if u:
            return u
        else:
            return await self.register(username)

    async def create_category(self, name: str, description: str):
        cat = {"id": len(category["data"]) + 1, "name": name}
        category["data"].append(cat)

        return cat

    async def get_categories(self):
        """
        查询帖子分类
        """
        return category

    async def delete_category(self, category_id: str):
        """
        删除帖子分类
        """
        category["data"] = [c for c in category["data"] if c["id"] != int(category_id)]
        return category

    async def create_thread(self, title: str, content: str, category_id: int):
        t = {"id": len(threads) + 1, "title": title, "content": content, "category_id": category_id, "posts": []}
        threads.append(t)
        return t

    async def update_thread(self, thread_id, title=""):
        for t in threads:
            if t["id"] == thread_id:
                t["title"] = title
                return t

    async def delete_thread(self, thread_id: str):
        """
        删除主题
        """

        global threads
        threads = [t for t in threads if t["id"] != thread_id]
        return {"id": thread_id}

    async def get_thread(self, thread_id):
        """
        获得主题
        """
        for t in threads:
            if t["id"] == thread_id:
                return t
        return None

    async def get_post_replies(self, rid, skip, limit):
        """
        获得楼中楼回复
        """
        res = []
        for t in threads:
            for p in t["posts"]:
                if p["reply_id"] == rid:
                    res.append(p)

        return res

    async def get_post_from_thread(self, thread_id, skip, limit):
        """
        获得主题一级评论
        """
        for t in threads:
            if t["id"] == thread_id:
                return t["posts"]
        return []

    async def create_post(self, content, thread_id, reply_id=0):
        for t in threads:
            if t["id"] == thread_id:
                p = {"id": len(t["posts"]) + 1, "content": content, "reply_id": reply_id}
                t["posts"].append(p)
                return p

    async def delete_post(self, pid):
        for t in threads:
            t["posts"] = [p for p in t["posts"] if p["id"] != pid]

    async def update_post_content(self, pid, content):
        for t in threads:
            for p in t["posts"]:
                if p["id"] == pid:
                    p["content"] = content
                    return p

    async def like_post(self, post_id):
        """
        点赞帖子或主题
        """
        for t in threads:
            for p in t["posts"]:
                if p["id"] == post_id:
                    p["liked"] = True

    async def unlike_post(self, post_id):
        """
        取消点赞
        """
        for t in threads:
            for p in t["posts"]:
                if p["id"] == post_id:
                    p["liked"] = False

    async def unmark_thread(self, thread_id):
        """
        取消收藏主题
        """
        for t in threads:
            if t["id"] == thread_id:
                t["marked"] = False

    async def bookmark_thread(self, thread_id):
        for t in threads:
            if t["id"] == thread_id:
                t["marked"] = True

    async def my_bookmarked_threads(self, skip, limit):
        return {"data": [t for t in threads if "marked" in t and t["marked"] is True]}

    async def my_like_posts(self, skip, limit):
        return {"data": [p for t in threads for p in t["posts"] if "liked" in p and p["liked"] is True]}
