from pytest import mark

from app.crud.base import get_user_collection
from app.service.disc import check_article_exist, clear_error_article

pytestmark = mark.asyncio


async def test_check_article_exist(fixture_client, fixture_portfolio):
    flag = await check_article_exist("1")
    assert flag is True
    flag = await check_article_exist(fixture_portfolio["article_id"])
    assert flag is False


async def test_clear_error_article(fixture_client, fixture_db, fixture_user_data):
    user = await get_user_collection(fixture_db).find_one({"username": fixture_user_data["username"]})
    assert user["disc_id"] is fixture_user_data["disc_id"]
    await clear_error_article(fixture_db, get_user_collection, {"username": fixture_user_data["username"]}, "disc_id")
    user = await get_user_collection(fixture_db).find_one({"username": fixture_user_data["username"]})
    assert user["disc_id"] is None
