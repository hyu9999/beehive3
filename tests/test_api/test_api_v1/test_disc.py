from datetime import datetime

import pytest
from pytest import mark

from app.core.discuzqlib.exception import DiscuzqError
from app.core.errors import DiscuzqCustomError
from app.enums.disc import 社区文章动作
from tests.mocks.disc import MockUpDiscClient


def test_get_article_stream_view(fixture_client, free_user_headers, mocker):
    async def mock_get_thread_reply_ids(*args):
        return {
            "count": 2,
            "data": ["33", "34"],
            "skip": 0,
            "limit": 10,
        }

    article_id = "32"
    m_func = mocker.patch("app.api.api_v1.endpoints.disc.get_thread_reply_ids", side_effect=mock_get_thread_reply_ids)
    response = fixture_client.get(f"disc/article/{article_id}/stream", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert m_func.called


def test_get_topic_posts_view(fixture_client, free_user_headers, mocker):
    async def mock_get_thread_replies(*args):
        return [
            {
                "post_number": "11",
                "display_username": "display_username",
                "cooked": "cooked",
                "created_at": "2021-04-14T17:26:08+08:00",
                "like_count": 10,
                "is_self": True,
                "is_liked": True,
            }
        ]

    article_id = "1"
    username = "username"
    m_func = mocker.patch("app.api.api_v1.endpoints.disc.get_thread_replies", side_effect=mock_get_thread_replies)
    response = fixture_client.get(f"disc/article/{article_id}/{username}/posts", params={"post_ids": [1]}, headers=free_user_headers)
    assert response.status_code == 200
    assert m_func.called


def test_get_post_replies_view(fixture_client, free_user_headers, mocker):
    async def mock_get_post_replies(*args):
        return [
            {
                "post_number": "11",
                "display_username": "display_username",
                "cooked": "cooked",
                "created_at": "2021-04-14T17:26:08+08:00",
                "like_count": 10,
            }
        ]

    m_func = mocker.patch("app.api.api_v1.endpoints.disc.get_post_replies", side_effect=mock_get_post_replies)
    post_id = 11
    response = fixture_client.get(f"disc/post/{post_id}/replies", headers=free_user_headers)
    assert response.status_code == 200
    assert m_func.called


@mark.parametrize("action", [社区文章动作.like, 社区文章动作.unlike, 社区文章动作.bookmark])
def test_topic_action_view(fixture_client, free_user_headers, mocker, action):
    async def mock_action(*args):
        ...

    async def mock_exception_action(*args):
        raise DiscuzqCustomError()

    article_id, username = 1, "username"
    if action not in [社区文章动作.like, 社区文章动作.unlike]:
        response = fixture_client.post(f"disc/article/{article_id}/{username}/actions/{action}", headers=free_user_headers)
        assert response.status_code == 200
        assert response.json()["result"] == "failure"
    else:
        # 成功
        m_func = mocker.patch(f"app.api.api_v1.endpoints.disc.{action}_post", side_effect=mock_action)
        response = fixture_client.post(f"disc/article/{article_id}/{username}/actions/{action}", headers=free_user_headers)
        assert response.status_code == 200
        assert response.json()["result"] == "success"
        assert m_func.called
        # 失败
        mocker.patch(f"app.api.api_v1.endpoints.disc.{action}_post", side_effect=mock_exception_action)
        response = fixture_client.post(f"disc/article/{article_id}/{username}/actions/{action}", headers=free_user_headers)
        assert response.status_code == 400


def test_create_post_view(fixture_client, free_user_headers, mocker):
    async def mock_create_post(*args, **kwargs):
        return {
            "display_username": "display_username",
            "cooked": "raw",
            "created_at": "2021-04-14T17:26:08+08:00",
            "like_count": 0,
            "is_liked": False,
            "is_self": True,
            "post_id": "post_id",
        }

    m_func = mocker.patch("app.api.api_v1.endpoints.disc.create_post", side_effect=mock_create_post)
    username = "username"
    response = fixture_client.post(f"disc/post/{username}", json={"post_id": "1", "raw": "raw", "reply_id": 0}, headers=free_user_headers)
    assert response.status_code == 201
    assert m_func.called
