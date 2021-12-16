import copy
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from bson import ObjectId
from pytest import fixture, mark
from stralib import FastTdate

from app.crud.fund_account import create_fund_account, create_fund_account_flow, create_fund_account_position
from app.crud.portfolio import create_portfolio
from app.crud.time_series_data import (
    create_fund_time_series_data,
    create_portfolio_assessment_time_series_data,
)
from app.db.mongodb import get_database
from app.enums.fund_account import FlowTType
from app.enums.portfolio import PortfolioCategory, 组合状态
from app.models.fund_account import FundAccountFlowInDB, FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyDecimal, PyObjectId
from app.models.time_series_data import PortfolioAssessmentTimeSeriesDataInDB
from app.schema.user import User
from app.service.datetime import get_early_morning
from app.utils.datetime import date2datetime
from tests.consts.robots import robot_test_data, const_robot
from tests.test_helper import get_random_str

pytestmark = mark.asyncio


@fixture
def portfolio_data_in_create():
    """组合创建基础数据"""
    return {
        "portfolio": {
            "name": "test_portfolio_1",
            "initial_funding": 500000,
            "tags": ["test_自定义标签1", "test_自定义标签1", "test_自定义标签2"],
            "introduction": "组合介绍",
            "config": {"max_period": "90", "expected_return": 0.2},
            "robot_config": {"adjust_cycle": "60", "max_quantity": "5"},
            "robot": robot_test_data["标识符"],
            "is_open": False,
            "activity": "5e8142c92f2facb43b8d0f82",
        }
    }


@fixture
def portfolio_data_in_db():
    """数据库中组合数据"""
    return {
        "_id": PyObjectId(),
        "name": "test_portfolio_2",
        "status": 组合状态.running,
        "username": "test_VIP用户",
        "fund_account": [
            {
                "userid": "test_fund",
                "fundid": str(ObjectId()),
                "create_date": datetime.utcnow().strftime("%Y%m%d"),
            }
        ],
        "initial_funding": 500000,
        "invest_type": "stock",
        "tags": ["test_自定义标签2", "test_自定义标签1"],
        "introduction": "组合介绍",
        "config": {"max_period": "90", "expected_return": 0.2},
        "robot_config": {"adjust_cycle": "60", "max_quantity": "5", "open_risks": []},
        "risks": [],
        "is_open": False,
        "robot": robot_test_data["标识符"],
        "subscribe_num": "0",
        "article_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "activity": PyObjectId("5e8142c92f2facb43b8d0f82"),
        "create_date": datetime.utcnow(),
        "close_date": datetime.utcnow() + timedelta(days=90),
        "import_date": datetime.utcnow(),
    }


@fixture
def portfolio_with_self_robot_data_in_db():
    """数据库中组合数据"""
    return {
        "_id": PyObjectId(),
        "name": "test_portfolio_3",
        "status": 组合状态.running,
        "username": "test_free_user",
        "fund_account": [
            {
                "userid": "test_fund",
                "fundid": str(ObjectId()),
                "create_date": datetime.utcnow().strftime("%Y%m%d"),
            }
        ],
        "initial_funding": 500000,
        "invest_type": "stock",
        "tags": ["test_自定义标签2", "test_自定义标签1"],
        "introduction": "组合介绍",
        "config": {"max_period": "90", "expected_return": 0.2},
        "robot_config": {"adjust_cycle": "60", "max_quantity": "5", "open_risks": []},
        "risks": [],
        "is_open": False,
        "robot": const_robot["only_screen"]["标识符"],
        "subscribe_num": "0",
        "article_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "activity": PyObjectId("5e8142c92f2facb43b8d0f82"),
        "create_date": datetime.utcnow(),
        "close_date": datetime.utcnow() + timedelta(days=90),
        "import_date": datetime.utcnow(),
    }


@fixture
def manual_portfolio_data_in_db():
    """手动录入数据的组合数据"""
    return {
        "_id": PyObjectId(),
        "name": "test_manual_portfolio",
        "status": 组合状态.running,
        "username": "test_free_user",
        "fund_account": {
            "userid": "test_fund",
            "fundid": str(ObjectId()),
            "create_date": datetime.utcnow().strftime("%Y%m%d"),
        },
        "initial_funding": 0,
        "invest_type": "stock",
        "tags": ["test_自定义标签2", "test_自定义标签1"],
        "introduction": "组合介绍",
        "config": {"max_period": "90", "expected_return": 0.2},
        "robot_config": {"adjust_cycle": "60", "max_quantity": "5", "open_risks": []},
        "risks": [],
        "is_open": False,
        "robot": robot_test_data["标识符"],
        "subscribe_num": "0",
        "article_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "stats_data": {
            "last_tdate": {"trade_stats": {}, "stock_stats": []},
            "last_week": {"trade_stats": {}, "stock_stats": []},
            "last_month": {"trade_stats": {}, "stock_stats": []},
            "last_3_month": {"trade_stats": {}, "stock_stats": []},
            "last_half_year": {"trade_stats": {}, "stock_stats": []},
            "last_year": {"trade_stats": {}, "stock_stats": []},
        },
        "activity": PyObjectId("5e8142c92f2facb43b8d0f82"),
        "create_date": datetime.utcnow(),
        "close_date": datetime.utcnow() + timedelta(days=90),
        "import_date": datetime.utcnow(),
    }


@fixture
def stock_log_data_in_db():
    return {
        "symbol": "601515",
        "symbol_name": "东风股份",
        "order_quantity": 100,
        "exchange": "1",
        "order_id": "test_order_id",
        "order_time": "093509",
        "order_direction": "buy",
        "order_price": 7,
        "order_status": "2",
        "trade_time": "131121",
        "trade_price": 7,
        "trade_volume": 100,
        "stkeffect": 100,
        "fundeffect": -706,
        "stamping": 0,
        "transfer_fee": 1,
        "commission": 5,
        "total_fee": 6,
        "filled_amt": 706,
        "settlement_fee": 0,
        "order_date": "20191018",
        "ttype": "3",
    }


@fixture
def stock_log_dict(fixture_portfolio):
    return {
        "_id": str(PyObjectId()),
        "symbol": "601515",
        "symbol_name": "东风股份",
        "order_quantity": "100",
        "exchange": "1",
        "order_id": "test_order_id",
        "order_time": "093509",
        "order_direction": "buy",
        "order_price": 7,
        "order_status": "2",
        "trade_time": "131121",
        "trade_price": 7,
        "trade_volume": "100",
        "stkeffect": "100",
        "fundeffect": -706,
        "stamping": 0,
        "transfer_fee": 1,
        "commission": 5,
        "total_fee": 6,
        "filled_amt": 706,
        "settlement_fee": 0,
        "trade_date": "20191018",
        "ttype": "3",
        "portfolio": fixture_portfolio["_id"],
    }


@fixture
def fixture_stock_log(fixture_client, fixture_db, fixture_settings, fixture_portfolio, stock_log_dict):
    stock_log_in_db = copy.deepcopy(stock_log_dict)
    stock_log_in_db["_id"] = PyObjectId(stock_log_in_db["_id"])
    stock_log_in_db["portfolio"] = PyObjectId(stock_log_in_db["portfolio"])

    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.STOCK_LOG].insert_one(stock_log_in_db)
    yield stock_log_in_db
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.STOCK_LOG].delete_one({"portfolio": stock_log_in_db["portfolio"]})


@fixture
def portfolio_sci_risk_data(portfolio_data_in_db):
    """
    含有止盈止损、调仓周期、个股风险的组合数据
    """
    risks = [
        # 止盈风险
        {
            "id": PyObjectId(),
            "status": "11",
            "risk_type": "0",
            "symbol": "600100",
            "exchange": "1",
        },
        # 调仓周期风险
        {
            "id": PyObjectId(),
            "status": "11",
            "risk_type": "10",
            "symbol": "600200",
            "exchange": "1",
        },
        # 个股风险，股票已被st
        {
            "id": PyObjectId(),
            "status": "11",
            "risk_type": "5",
            "symbol": "600179",
            "exchange": "1",
        },
    ]
    sci_risk_data_in_db = copy.deepcopy(portfolio_data_in_db)
    sci_risk_data_in_db["_id"] = PyObjectId()
    sci_risk_data_in_db["risks"] = risks
    sci_risk_data_in_db["name"] = "test_portfolio_sci"
    return sci_risk_data_in_db


@fixture
def portfolio_overweight_risk_data(portfolio_data_in_db):
    """含有仓位过重风险的组合数据"""
    risks = [
        # 仓位过重
        {
            "id": PyObjectId(),
            "status": "11",
            "risk_type": "8",
            "symbol": "600200",
            "exchange": "1",
        },
    ]
    overweight_risk_data_in_db = copy.deepcopy(portfolio_data_in_db)
    overweight_risk_data_in_db["_id"] = PyObjectId()
    overweight_risk_data_in_db["risks"] = risks
    overweight_risk_data_in_db["name"] = "test_portfolio_overweight"
    return overweight_risk_data_in_db


@fixture
def portfolio_underweight_risk_data(portfolio_data_in_db):
    """含有仓位过轻风险的组合数据"""
    risks = [
        # 仓位过轻
        {
            "id": PyObjectId(),
            "status": "11",
            "risk_type": "9",
            "symbol": "600100",
            "exchange": "1",
        },
    ]
    underweight_risk_data_in_db = copy.deepcopy(portfolio_data_in_db)
    underweight_risk_data_in_db["_id"] = PyObjectId()
    underweight_risk_data_in_db["risks"] = risks
    underweight_risk_data_in_db["name"] = "test_portfolio_underweight"
    return underweight_risk_data_in_db


async def _create_portfolio(db, fixture_settings, data, stock_data=None):
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.PORTFOLIO].insert_one(data)
    if stock_data:
        stock_data["trade_date"] = datetime.utcnow().strftime("%Y%m%d")
        stock_data["portfolio"] = data["_id"]
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.STOCK_LOG].insert_one(stock_data)
    data["_id"] = str(data["_id"])
    return data


async def _delete_portfolio(db, fixture_settings, portfolio_id: PyObjectId):
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.PORTFOLIO].delete_many({"_id": portfolio_id})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.PORTFOLIO_ACCOUNT].delete_many({"portfolio": portfolio_id})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.STOCK_LOG].delete_many({"portfolio": portfolio_id})


@fixture
async def fixture_portfolio(fixture_client, fixture_settings, portfolio_data_in_db):
    """创建组合，返回组合详情，测试结束清除组合相关测试数据"""
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, portfolio_data_in_db)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, portfolio_data_in_db["_id"])


@fixture
async def fixture_portfolio_with_self_robot(fixture_client, fixture_settings, portfolio_with_self_robot_data_in_db):
    """创建组合，返回组合详情，测试结束清除组合相关测试数据"""
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, portfolio_with_self_robot_data_in_db)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, portfolio_with_self_robot_data_in_db["_id"])


@fixture
async def fixture_manual_portfolio(fixture_client, fixture_settings, manual_portfolio_data_in_db):
    """创建组合，返回组合详情，测试结束清除组合相关测试数据"""
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, manual_portfolio_data_in_db)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, manual_portfolio_data_in_db["_id"])


@fixture
async def fixture_portfolio_sci_risk(fixture_client, fixture_settings, portfolio_sci_risk_data):
    """含有止盈止损、调仓周期、个股风险的组合"""
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, portfolio_sci_risk_data)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, portfolio_sci_risk_data["_id"])


@fixture
async def fixture_portfolio_overweight_risk(fixture_client, fixture_settings, portfolio_overweight_risk_data):
    """含有仓位过重风险的组合"""
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, portfolio_overweight_risk_data)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, portfolio_overweight_risk_data["_id"])


@fixture
async def fixture_portfolio_underweight_risk(fixture_client, fixture_settings, portfolio_underweight_risk_data):
    """含有仓位过轻风险的组合"""
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, portfolio_underweight_risk_data)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, portfolio_underweight_risk_data["_id"])


@fixture
async def fixture_portfolio_new_stock(fixture_client, fixture_settings, portfolio_data_in_db):
    """普通组合"""
    db = await get_database()
    portfolio_data_in_db.update({"name": "test_portfolio_new_stock"})
    portfolio = await _create_portfolio(db, fixture_settings, portfolio_data_in_db)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, portfolio_data_in_db["_id"])


@fixture
async def fixture_stock_portfolio(
    fixture_client,
    fixture_settings,
    portfolio_data_in_db,
    stock_log_data_in_db,
):
    """创建有stock_log的组合，返回组合详情，测试结束清除组合相关测试数据"""
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, portfolio_data_in_db, stock_log_data_in_db)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, portfolio_data_in_db["_id"])


@fixture
async def fixture_off_line_portfolio(fixture_client, fixture_settings, portfolio_data_in_db):
    """创建已下线状态的组合，返回组合详情"""
    off_line_portfolio_data = portfolio_data_in_db.copy()
    off_line_portfolio_data.update({"name": "test_off_line_portfolio", "status": 组合状态.closed, "_id": PyObjectId()})
    db = await get_database()
    portfolio = await _create_portfolio(db, fixture_settings, off_line_portfolio_data)
    yield portfolio
    await _delete_portfolio(db, fixture_settings, off_line_portfolio_data["_id"])


@fixture
def fixture_user_data(fixture_client, fixture_db, fixture_settings):
    """用户基础数据"""
    data = {
        "mobile": "15600000000",
        "username": "test_user_156",
        "api_key": fixture_settings.auth.api_key,
        "roles": ["免费用户"],
        "disc_id": 0,
    }
    response = fixture_client.post("/api/user/register", json={"user": data})
    assert response.status_code == 201
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.USER].update_one({"username": data["username"]}, {"$set": {"disc_id": 0}})
    yield data
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.USER].delete_one({"username": data["username"]})


@pytest.fixture
async def portfolio_in_db(fixture_db, portfolio_data_in_db, logined_vip_user) -> Portfolio:
    portfolio_data_in_db = copy.deepcopy(portfolio_data_in_db)
    portfolio_data_in_db["username"] = logined_vip_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    return portfolio


@pytest.fixture
async def portfolio_with_user(fixture_db, portfolio_data_in_db, logged_in_free_user):
    portfolio_data_in_db = copy.deepcopy(portfolio_data_in_db)
    portfolio_data_in_db["username"] = logged_in_free_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    return portfolio, User(**logged_in_free_user["user"])


@pytest.fixture
async def portfolio_with_fund_account(fixture_db, fund_account_data, portfolio_data_in_db, logged_in_free_user):
    fund_asset = await create_fund_account(fixture_db, FundAccountInDB(**fund_account_data))
    portfolio_data_in_db["category"] = PortfolioCategory.ManualImport.value
    portfolio_data_in_db["name"] = get_random_str()
    portfolio_data_in_db["fund_account"][0]["fundid"] = str(fund_asset.id)
    portfolio_data_in_db["username"] = logged_in_free_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    return portfolio, fund_asset


@pytest.fixture
async def portfolio_with_fund_time_series_data(fixture_db, portfolio_with_fund_account, fund_time_series_data_list):
    portfolio, fund_account = portfolio_with_fund_account
    tdate = datetime.today().date()
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(tdate - timedelta(days=100), tdate)
    fund_time_series_data_list = copy.deepcopy(fund_time_series_data_list)
    cash_line = [0, 100000, 200000, 250000]
    for index, item in enumerate(fund_time_series_data_list):
        item.fund_id = str(fund_account.id)
        item.fundbal = PyDecimal(item.fundbal.to_decimal() + Decimal(cash_line[index]))
        await create_fund_time_series_data(fixture_db, item)
    return portfolio, fund_account, fund_time_series_data_list, (day1, day2, day3, day4)


@pytest.fixture
async def portfolio_with_flow(
    fixture_db,
    fund_account_data,
    logged_in_free_user,
    fund_account_flow_data,
    portfolio_data_in_db,
):
    fund_asset = await create_fund_account(fixture_db, FundAccountInDB(**fund_account_data))
    portfolio_data_in_db = copy.deepcopy(portfolio_data_in_db)
    portfolio_data_in_db["category"] = PortfolioCategory.ManualImport.value
    portfolio_data_in_db["name"] = get_random_str()
    portfolio_data_in_db["fund_account"][0]["fundid"] = str(fund_asset.id)
    portfolio_data_in_db["username"] = logged_in_free_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    fund_account_flow_data = copy.deepcopy(fund_account_flow_data)
    for ttype in FlowTType:
        fund_account_flow_data["ttype"] = ttype
        fund_account_flow_data["fund_id"] = str(fund_asset.id)
        fund_account_flow_data["fundeffect"] = 100000
        await create_fund_account_flow(fixture_db, FundAccountFlowInDB(**fund_account_flow_data))
    return portfolio


@pytest.fixture
async def portfolio_for_target_data(fixture_db, portfolio_with_fund_time_series_data):
    portfolio, _, asset_time_series_data_list, _ = portfolio_with_fund_time_series_data
    tdate = get_early_morning()
    assessment_in_db = PortfolioAssessmentTimeSeriesDataInDB(portfolio=portfolio.id, tdate=tdate)
    await create_portfolio_assessment_time_series_data(fixture_db, assessment_in_db)
    assessment_in_db.tdate = date2datetime(FastTdate.last_tdate(tdate))
    await create_portfolio_assessment_time_series_data(fixture_db, assessment_in_db)
    return portfolio


@pytest.fixture
async def portfolio_with_position(fixture_db, portfolio_with_fund_account, fund_account_position_data):
    portfolio, fund_asset = portfolio_with_fund_account
    position = FundAccountPositionInDB(**fund_account_position_data)
    position.fund_id = str(fund_asset.id)
    symbol_list = ["600001", "600002", "600003", "600519"]
    position_list = []
    for symbol in symbol_list:
        position.symbol = symbol
        position_in_db = await create_fund_account_position(fixture_db, position)
        position_list.append(position_in_db)
    return portfolio, fund_asset, position_list
