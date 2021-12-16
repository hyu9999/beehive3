from typing import Dict

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field

from app.schema.post import PostInResponse


async def mock_create_thread(*args, **kwargs):
    return PostInResponse(id=1).dict()


async def mock_get_or_create_disc_user(username):
    return 1


async def mock_update_user_signature(*args, **kwargs):
    ...


async def mock_clear_error_article(conn: AsyncIOMotorClient, collection, filters, name):
    pass


def mock_disc_category(*args):
    return {"组合": {"测试组合": "111"}}


class MockDisc:
    base_url: str = Field(..., env="discuzq_base_url")  # 社区url
    admin: str = Field(..., env="discuzq_admin")
    password: str = Field(..., env="discuzq_password")
    switch: str = Field(..., env="discuzq_switch")  # 社区启用开关
    category: Dict[str, int] = Field(..., env="discuzq_category")

    @property
    def category(self):
        return {"组合": "111", "装备": "222", "机器人": "333"}
