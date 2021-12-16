import pytest

from app.service.robots.robot import generate_robot_version

pytestmark = pytest.mark.asyncio


async def test_generate_robot_version(fixture_online_robot: dict):
    pass
