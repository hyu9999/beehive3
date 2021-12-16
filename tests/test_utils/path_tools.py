import os

from pytest import mark

from app.utils.path_tools import get_file_path

pytestmark = mark.asyncio


async def test_get_file_path(fixture_client):
    files = get_file_path(".", os.path.basename(__file__))
    assert os.path.basename(__file__) in files[0]
