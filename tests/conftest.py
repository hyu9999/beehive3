import asyncio
import contextlib
import enum
import inspect
from copy import deepcopy

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from starlette.config import environ
from starlette.testclient import TestClient

from app import get_settings
from app.crud.base import get_user_collection
from app.crud.user import create_manufacturer_user, create_user, delete_user
from app.db.mongodb import get_database
from app.schema.user import ManufacturerUserInCreate, UserInCreate
from tests.test_helper import drop_test_db, get_header, get_random_str, init_test_db

# 引入fixtures包下文件，使文件中fixture可全局共享
pytest_plugins = [
    "tests.fixtures.portfolio",
    "tests.fixtures.robot",
    "tests.fixtures.activity",
    "tests.fixtures.equipment",
    "tests.fixtures.tag",
    "tests.fixtures.fund_account",
    "tests.fixtures.strategy_data",
    "tests.mocks.mock_response",
    "tests.mocks.mock_redis",
]

mobile = 15500000000


class FakeRoles(enum.Enum):
    免费用户 = "免费用户"
    VIP用户 = "VIP用户"
    厂商用户 = "厂商用户"
    超级用户 = "超级用户"
    策略管理员 = "策略管理员"


class FakeUser:
    @classmethod
    def _base_user(cls, settings):
        global mobile
        mobile = mobile + 1
        return {
            "mobile": str(mobile),
            "username": f"test_{inspect.currentframe().f_code.co_name}",
            "api_key": settings.auth.api_key,
            "password": "test12345",
            "app_secret": settings.mfrs.APP_SECRET,
            "code": settings.sms.fixed_code,
        }

    @classmethod
    def user(cls, settings, user_role: FakeRoles):
        user = cls._base_user(settings)
        user["username"] = f"test_{user_role.value}"
        user["nickname"] = f"用户{user['mobile'][-4:]}"
        return {"user": user, "role": user_role.value}


@pytest.fixture(scope="session")
def fixture_settings():
    settings = get_settings()
    settings.db.DB_NAME = settings.db.TEST_DB_NAME
    settings.hq.source = "Fakehq"
    settings.trade_url = "http://fake_trade_system.com"
    settings.vip_code = get_random_str()
    settings.discuzq.switch = True
    settings.mfrs.APP_SECRET = "111111"
    settings.sms.switch = False
    settings.num_limit = {
        "免费用户": {"portfolio": 0},
        "VIP用户": {"portfolio": 10, "equipment": 5, "robot": 5},
    }
    yield settings


@pytest.fixture(scope="session")
def free_user_data(fixture_settings):
    """免费用户基础数据"""
    return FakeUser.user(fixture_settings, FakeRoles.免费用户)


@pytest.fixture(scope="session")
def vip_user_data(fixture_settings):
    """vip用户基础数据"""
    return FakeUser.user(fixture_settings, FakeRoles.VIP用户)


@pytest.fixture(scope="session")
def client_user_data(fixture_settings):
    """client用户基础数据"""
    return FakeUser.user(fixture_settings, FakeRoles.厂商用户)


@pytest.fixture(scope="session")
def client_user_by_delete(fixture_settings):
    """client用户基础数据 用于删除使用"""
    return FakeUser.user(fixture_settings, FakeRoles.厂商用户)


@pytest.fixture(scope="session")
def airflow_user_data(fixture_settings):
    """airflow用户基础数据"""
    return FakeUser.user(fixture_settings, FakeRoles.策略管理员)


@pytest.fixture(scope="session")
def root_user_data(fixture_settings):
    """root用户基础数据"""
    return FakeUser.user(fixture_settings, FakeRoles.超级用户)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def initialized_app(fixture_settings, vip_user_data) -> FastAPI:
    from app.main import app

    async with LifespanManager(app, startup_timeout=30):
        db = await get_database()
        await drop_test_db(fixture_settings, db)
        await init_test_db(fixture_settings, db, vip_user_data["user"]["username"])
        try:
            yield app
        except contextlib.suppress(Exception):
            ...
        finally:
            await drop_test_db(fixture_settings, db)


@pytest.fixture(scope="module")
def fixture_client(initialized_app, fixture_settings, event_loop):
    base_url = f"http://{fixture_settings.host}:{fixture_settings.port}{fixture_settings.url_prefix}/"
    with TestClient(initialized_app, base_url=base_url) as fixture_client:
        yield fixture_client


@pytest.fixture(scope="module")
async def client(initialized_app, fixture_settings) -> AsyncClient:
    base_url = f"http://{fixture_settings.host}:{fixture_settings.port}{fixture_settings.url_prefix}/"
    async with AsyncClient(
        app=initialized_app,
        base_url=base_url,
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest.fixture
def authorized_client(client: AsyncClient, fixture_settings, logined_vip_user):
    client.headers = get_header(fixture_settings, logined_vip_user)
    yield client


@pytest.fixture(scope="module")
def fixture_db(fixture_client, event_loop):

    return event_loop.run_until_complete(get_database())


def _login_user(fixture_client, event_loop, db, user_data: dict, mocker):
    """创建用户、登录，返回用户详情"""
    try:
        role = user_data["role"]
        if role == "厂商用户":
            user = ManufacturerUserInCreate(**user_data["user"])
            event_loop.run_until_complete(create_manufacturer_user(db, user, role))
        else:
            user = UserInCreate(**user_data["user"])
            event_loop.run_until_complete(create_user(db, user, role))
    except DuplicateKeyError:
        pass
    response = fixture_client.post("/api/auth/login", json=user_data)
    assert response.status_code == 200
    return response.json()


async def get_logged_in_user(client: AsyncClient, db: AsyncIOMotorClient, user_dict: dict):
    try:
        role = user_dict["role"]
        if role == "厂商用户":
            user = ManufacturerUserInCreate(**user_dict["user"])
            await create_manufacturer_user(db, user, role)
        else:
            user = UserInCreate(**user_dict["user"])
            await create_user(db, user, role)
    except DuplicateKeyError as e:
        raise ValueError("获取登录用户失败.") from e
    else:
        response = await client.post("auth/login", json=user_dict)
        assert response.status_code == 200
        return response.json()


@pytest.fixture
def logined_free_user(fixture_client, event_loop, fixture_db, free_user_data):
    """注册一个免费用户并且用这个用户登录，用户测试需要登录权限的情况"""
    response = fixture_client.post("/api/user/register", json=free_user_data)
    assert response.status_code == 201
    response = fixture_client.post("/api/auth/login", json=free_user_data)
    assert response.status_code == 200
    yield response.json()
    event_loop.run_until_complete(delete_user(fixture_db, free_user_data["user"]["username"]))


@pytest.fixture
def logined_vip_user(fixture_client, event_loop, fixture_db, vip_user_data, mocker):
    """注册一个vip用户并且用这个用户登录，用户测试需要登录权限的情况"""
    yield _login_user(fixture_client, event_loop, fixture_db, vip_user_data, mocker)
    event_loop.run_until_complete(delete_user(fixture_db, vip_user_data["user"]["username"]))


@pytest.fixture
def logined_client_user(fixture_client, event_loop, fixture_db, client_user_data, mocker):
    """注册一个vip用户并且用这个用户登录，用户测试需要登录权限的情况"""
    yield _login_user(fixture_client, event_loop, fixture_db, client_user_data, mocker)
    event_loop.run_until_complete(delete_user(fixture_db, client_user_data["user"]["username"]))


@pytest.fixture
async def logged_in_client_user(client, event_loop, fixture_db, client_user_data):
    user = deepcopy(client_user_data)
    user["user"]["username"] = get_random_str()
    logged_in_user_data = await get_logged_in_user(client, fixture_db, user)
    await get_user_collection(fixture_db).update_one(
        {"username": user["user"]["username"]},
        {"$set": {"client_name": "建投测试厂商"}},
    )
    yield logged_in_user_data
    await delete_user(fixture_db, user["user"]["username"])


@pytest.fixture
async def logged_in_free_user(client, event_loop, fixture_db, free_user_data):
    user = deepcopy(free_user_data)
    user["user"]["username"] = get_random_str()
    logged_in_user_data = await get_logged_in_user(client, fixture_db, user)
    yield logged_in_user_data
    await delete_user(fixture_db, user["user"]["username"])


@pytest.fixture
async def logged_in_root_user(client, event_loop, fixture_db, root_user_data):
    user = deepcopy(root_user_data)
    user["user"]["username"] = get_random_str()
    logged_in_user_data = await get_logged_in_user(client, fixture_db, user)
    yield logged_in_user_data
    await delete_user(fixture_db, user["user"]["username"])


@pytest.fixture
def logined_airflow_user(fixture_client, event_loop, fixture_db, airflow_user_data, mocker):
    """注册airflow用户并登录，返回token"""
    yield _login_user(fixture_client, event_loop, fixture_db, airflow_user_data, mocker)
    event_loop.run_until_complete(delete_user(fixture_db, airflow_user_data["user"]["username"]))


@pytest.fixture
def logined_root_user(fixture_client, event_loop, fixture_db, root_user_data, mocker):
    """注册root用户并登录，返回token"""
    yield _login_user(fixture_client, event_loop, fixture_db, root_user_data, mocker)
    event_loop.run_until_complete(delete_user(fixture_db, root_user_data["user"]["username"]))


@pytest.fixture
def free_user_headers(fixture_settings, logined_free_user):
    """免费用户HTTP Authorization请求标头"""
    return get_header(fixture_settings, logined_free_user)


@pytest.fixture
def vip_user_headers(fixture_settings, logined_vip_user):
    """vip用户HTTP Authorization请求标头"""
    return get_header(fixture_settings, logined_vip_user)


@pytest.fixture
def client_user_headers(fixture_settings, logined_client_user):
    """厂商用户HTTP Authorization请求标头"""
    return get_header(fixture_settings, logined_client_user)


@pytest.fixture
def airflow_user_headers(fixture_settings, logined_airflow_user):
    """airflow用户HTTP Authorization请求标头"""
    return get_header(fixture_settings, logined_airflow_user)


@pytest.fixture
def root_user_headers(fixture_settings, logined_root_user):
    """root用户HTTP Authorization请求标头"""
    return get_header(fixture_settings, logined_root_user)


# This line would raise an error if we use it after 'settings' has been imported.
environ["TESTING"] = "TRUE"
