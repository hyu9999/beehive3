import fakeredis.aioredis
import pytest


@pytest.fixture(autouse=True, scope="session")
def fake_redis(session_mocker):
    mock_aioredis = session_mocker.patch("app.db.redis.aioredis")

    async def mock_create_redis_pool(*args, **kwargs):
        return await fakeredis.aioredis.create_redis_pool()

    mock_aioredis.create_redis_pool.side_effect = mock_create_redis_pool
