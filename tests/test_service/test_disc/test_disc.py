import pytest

from app.core.discuzqlib.client import DiscuzqClient
from tests.mocks.disc import MockUpDiscClient


@pytest.fixture
def discuz_client():
    return MockUpDiscClient()


@pytest.mark.asyncio
async def test_user_create(discuz_client):
    # create user
    user = await discuz_client.register("user1", "testpassword")
    res = await discuz_client.get_user("user1")
    assert res["id"] == user["id"]


@pytest.mark.asyncio
async def test_user_delete(discuz_client):
    # remove client
    user = await discuz_client.get_user("user1")
    await discuz_client.delete_user(user["id"])
    res = await discuz_client.get_user("user1")
    assert res == {}


@pytest.mark.asyncio
async def test_category_create(discuz_client):
    # create category
    cat = await discuz_client.create_category("category", "a category for test")
    categories = await discuz_client.get_categories()
    assert cat["id"] in [c["id"] for c in categories["data"]]


@pytest.mark.asyncio
async def test_category_delete(discuz_client):
    categories = await discuz_client.get_categories()
    await discuz_client.delete_category([str(c["id"]) for c in categories["data"] if c["name"] == "category"][0])
    categories = await discuz_client.get_categories()
    assert [c["id"] for c in categories["data"] if c["name"] == "category"] == []


@pytest.mark.asyncio
async def test_thread_create_update_and_update(discuz_client):
    thread = await discuz_client.create_thread("test", "test", 1)
    res = await discuz_client.get_thread(thread["id"])
    assert thread["id"] == res["id"]

    await discuz_client.update_thread(thread["id"], title="updated title")
    res = await discuz_client.get_thread(thread["id"])
    assert res["title"] == "updated title"

    deleted_thread = await discuz_client.delete_thread(res["id"])
    assert deleted_thread["id"] == res["id"]
    assert await discuz_client.get_thread(res["id"]) is None


@pytest.mark.asyncio
async def test_post_create_update_and_delete(discuz_client):
    thread = await discuz_client.create_thread("test", "test", 1)
    post = await discuz_client.create_post("test post", thread["id"])
    rely = await discuz_client.create_post("test reply", thread["id"], post["id"])

    new_thread = await discuz_client.update_thread(thread["id"], title="new thread")
    assert new_thread["title"] == "new thread"

    new_post = await discuz_client.update_post_content(post["id"], "new post content")
    assert new_post["content"] == "new post content"

    new_rely = await discuz_client.update_post_content(rely["id"], "new reply content")
    assert new_rely["content"] == "new reply content"

    posts = await  discuz_client.get_post_from_thread(thread["id"], 0, 100)
    assert posts[0]["id"] == new_post["id"]

    replies = await discuz_client.get_post_replies(new_post["id"], 0, 100)
    assert replies[0]["id"] == new_rely["id"]

    await discuz_client.delete_post(new_rely["id"])
    await discuz_client.delete_post(new_post["id"])
    await discuz_client.delete_thread(thread["id"])

    assert await discuz_client.get_thread(thread["id"]) is None
    assert await discuz_client.get_thread(new_post["id"]) is None
    assert await discuz_client.get_thread(new_rely["id"]) is None


@pytest.mark.asyncio
async def test_thread_action(discuz_client):
    # bookmark
    thread = await discuz_client.create_thread("test", "test", 1)
    post = await discuz_client.create_post("test post", thread["id"])

    await discuz_client.bookmark_thread(thread["id"])
    threads1 = await discuz_client.my_bookmarked_threads(0, 100)
    exist = False
    for t in threads1["data"]:
        if t["id"] == thread["id"]:
            exist = True
    assert exist is True

    await discuz_client.unmark_thread(thread["id"])
    threads2 = await discuz_client.my_bookmarked_threads(0, 100)

    exist = False
    for t in threads2["data"]:
        if t["id"] == thread["id"]:
            exist = True
    assert exist is False

    # like
    await discuz_client.like_post(post["id"])
    posts1 = await discuz_client.my_like_posts(0, 100)

    exist = False
    for t in posts1["data"]:
        if t["id"] == post["id"]:
            exist = True
    assert exist is True

    assert posts1["data"][0]["id"] == post["id"]
    await discuz_client.unlike_post(post["id"])
    posts2 = await discuz_client.my_like_posts(0, 100)

    exist = False
    for t in posts2["data"]:
        if t["id"] == post["id"]:
            exist = True
    assert exist is False

    await discuz_client.delete_post(post["id"])
    await discuz_client.delete_thread(thread["id"])


