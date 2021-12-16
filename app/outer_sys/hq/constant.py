from app.outer_sys.hq.hq_source.jiantou import JiantouHQ
from app.outer_sys.hq.hq_source.redis import RedisHQ
from tests.mocks.mock_hq import FakeHQ

HQ_SOURCE_MAPPING = {
    "Redis": RedisHQ,
    "Jiantou": JiantouHQ,
    "Fakehq": FakeHQ,
}
