from dataclasses import dataclass

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pytest import mark

from app.core.config import get
from app.core.errors import CreateQuantityLimit, PermissionDoesNotExist, ParamsError
from app.enums.common import 产品分类
from app.enums.equipment import 装备分类_3
from app.models.user import User
from app.service.create_limit import 创建数量限制

pytestmark = mark.asyncio


@dataclass
class MockCollection(object):

    conn: AsyncIOMotorClient
    config: str

    async def count_documents(self, *args, **kwargs):
        from app import settings

        return settings.num_limit["VIP用户"][get(self.config)]


@dataclass
class MockLittleCollection(object):

    conn: AsyncIOMotorClient
    config: str

    async def count_documents(self, *args, **kwargs):
        from app import settings

        return settings.num_limit["VIP用户"][get(self.config)] - 1


@mark.parametrize(
    "category, 装备分类, user",
    [
        (产品分类.equipment, 装备分类_3.选股, "免费用户"),
        (产品分类.robot, None, "VIP用户"),
        (产品分类.portfolio, None, "VIP用户"),
        (产品分类.equipment, 装备分类_3.选股, "VIP用户"),
        (产品分类.equipment, None, "VIP用户"),
        (产品分类.equipment, 装备分类_3.选股, "超级用户"),
    ],
)
async def test_check_create_quota_by_category(
    fixture_client, fixture_settings, fixture_db, logined_root_user, logined_free_user, logined_vip_user, category, 装备分类, user, mocker
):
    if user == "超级用户":
        response = await 创建数量限制(fixture_db, category, User(**logined_root_user["user"]), 装备分类)
        assert response is True
    elif user == "免费用户":
        with pytest.raises(PermissionDoesNotExist):
            await 创建数量限制(fixture_db, category, User(**logined_free_user["user"]), 装备分类)
    else:
        if category == 产品分类.equipment and 装备分类 is None:
            mocker.patch("app.service.create_limit.get_collection_by_config", side_effect=MockCollection)
            with pytest.raises(ParamsError):
                await 创建数量限制(fixture_db, category, User(**logined_vip_user["user"]), 装备分类)
        else:
            # wright
            mocker.patch("app.service.create_limit.get_collection_by_config", side_effect=MockLittleCollection)
            response = await 创建数量限制(fixture_db, category, User(**logined_vip_user["user"]), 装备分类)
            assert response is True
            # error
            mocker.patch("app.service.create_limit.get_collection_by_config", side_effect=MockCollection)
            with pytest.raises(CreateQuantityLimit):
                await 创建数量限制(fixture_db, category, User(**logined_vip_user["user"]), 装备分类)
