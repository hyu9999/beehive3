from copy import deepcopy
from datetime import datetime, timedelta
from typing import Tuple

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app.core.errors import (
    ActivityAlreadyJoined,
    PortfolioTooMany,
    RobotNoPermissionToUse,
)
from app.crud.activity import create_activity, get_activity_by_id
from app.crud.fund_account import (
    create_fund_account,
    create_fund_account_flow,
    create_fund_account_position,
)
from app.crud.portfolio import create_portfolio, delete_portfolio_many
from app.crud.time_series_data import create_portfolio_assessment_time_series_data
from app.enums.portfolio import PortfolioCategory
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.models.time_series_data import PortfolioAssessmentTimeSeriesDataInDB
from app.schema.activity import ActivityInCreate
from app.schema.portfolio import PortfolioBasicRunDataInResponse, PortfolioInResponse
from app.service.datetime import str_of_today
from app.utils.datetime import date2datetime
from tests.consts.activity import activity_in_create
from tests.consts.robots import robot_test_data
from tests.consts.time_series_data import portfolio_assessment_time_series_data_in_db
from tests.mocks.signal import mock_get_strategy_signal
from tests.test_helper import get_header, get_random_str

pytestmark = pytest.mark.asyncio


async def test_user_can_not_create_portfolio_if_the_number_of_portfolio_exceeds_the_limit(
    authorized_client,
    portfolio_data_in_create,
    mocker,
):
    del portfolio_data_in_create["portfolio"]["activity"]
    mock_settings = mocker.patch("app.service.portfolio.portfolio.settings")
    mock_settings.num_limit = {"VIP用户": {"portfolio": -1}}
    response = await authorized_client.post("portfolio", json=portfolio_data_in_create)
    assert mock_settings.assert_called
    assert response.status_code == 400
    assert response.json()["code"] == PortfolioTooMany.code


async def test_user_can_not_create_portfolio_if_activity_already_joined(
    client,
    portfolio_data_in_create,
    portfolio_data_in_db,
    logined_vip_user,
    fixture_settings,
    fixture_db,
):
    assert portfolio_data_in_create["portfolio"]["activity"]
    portfolio_data_in_db["username"] = logined_vip_user["user"]["username"]
    portfolio_data_in_db["activity"] = portfolio_data_in_create["portfolio"]["activity"]
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    client.headers = get_header(fixture_settings, logined_vip_user)
    response = await client.post("portfolio", json=portfolio_data_in_create)
    assert response.status_code == 400
    assert response.json()["code"] == ActivityAlreadyJoined.code


async def test_user_can_not_create_portfolio_if_no_robot_permission(
    client,
    portfolio_data_in_create,
    client_user_headers,
    fixture_settings,
    mocker,
    logined_free_user,
):
    client.headers = client_user_headers
    mock_setting = mocker.patch("app.dec.manufacturer_switch.settings")
    mock_setting.manufacturer_switch = True
    response = await client.post("portfolio", json=portfolio_data_in_create)
    assert mock_setting.assert_called
    assert response.status_code == 400
    assert response.json()["code"] == RobotNoPermissionToUse.code


@pytest.mark.parametrize(
    "category", [PortfolioCategory.ManualImport, PortfolioCategory.SimulatedTrading]
)
async def test_user_can_create_portfolio(
    category, authorized_client, portfolio_data_in_create
):
    del portfolio_data_in_create["portfolio"]["activity"]
    portfolio_data_in_create["portfolio"]["category"] = category.value
    response = await authorized_client.post("portfolio", json=portfolio_data_in_create)
    portfolio = Portfolio(**response.json())
    assert portfolio.name == portfolio_data_in_create["portfolio"]["name"]
    assert (
        portfolio.initial_funding
        == portfolio_data_in_create["portfolio"]["initial_funding"]
    )


async def test_user_can_join_activity(
    authorized_client, portfolio_data_in_create, fixture_db
):
    activity = await create_activity(fixture_db, ActivityInCreate(**activity_in_create))
    portfolio_data_in_create["portfolio"]["activity"] = str(activity.id)
    response = await authorized_client.post("portfolio", json=portfolio_data_in_create)
    portfolio = Portfolio(**response.json())
    activity = await get_activity_by_id(fixture_db, activity.id)
    assert portfolio.username in activity.participants


@pytest.mark.parametrize(
    "activity, result",
    [
        ("", 10),
        ("5e8142c92f2facb43b8d0f81", 1),
        ("5e8142c92f2facb43b8d0f82", 2),
        ("5e8142c92f2facb43b8d0f80", 0),
    ],
)
async def test_get_portfolio_list_filtering_by_activity(
    authorized_client, fixture_db, portfolio_data_in_db, activity, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["activity"] = "5e8142c92f2facb43b8d0f81"
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))

    portfolio_data_in_db["activity"] = "5e8142c92f2facb43b8d0f82"
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))

    portfolio_data_in_db["activity"] = "5e8142c92f2facb43b8d0f83"
    for i in range(7):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(f"portfolio?activity={activity}")
    portfolio_list = [
        PortfolioInResponse(**portfolio) for portfolio in response.json()["data"]
    ]
    assert len(portfolio_list) == result


@pytest.mark.parametrize(
    "status, result", [("", 3), ("running", 3), ("closed", 2), ("wrong", 0)]
)
async def test_get_portfolio_list_filtering_by_status(
    authorized_client, fixture_db, portfolio_data_in_db, status, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["status"] = "running"
    for i in range(3):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["status"] = "closed"
    for i in range(2):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(f"portfolio?status={status}")
    if result == 0:
        assert response.status_code == 422
    else:
        portfolio_list = [
            PortfolioInResponse(**portfolio) for portfolio in response.json()["data"]
        ]
        assert len(portfolio_list) == result


@pytest.mark.parametrize(
    "subscriber, result", [("", 4), ("user1", 3), ("user2", 2), ("wrong", 0)]
)
async def test_get_portfolio_list_filtering_by_subscriber(
    authorized_client, fixture_db, portfolio_data_in_db, subscriber, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["subscribers"] = ["user1", "user2"]
    for i in range(2):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["subscribers"] = ["user1"]
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["subscribers"] = ["user0"]
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(f"portfolio?subscriber={subscriber}")
    portfolio_list = [
        PortfolioInResponse(**portfolio) for portfolio in response.json()["data"]
    ]
    assert len(portfolio_list) == result


@pytest.mark.parametrize(
    "username, result", [("", 6), ("user1", 3), ("user2", 2), ("wrong", 0)]
)
async def test_get_portfolio_list_filtering_by_username(
    authorized_client, fixture_db, portfolio_data_in_db, username, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["username"] = "user1"
    for i in range(3):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["username"] = "user2"
    for i in range(2):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["username"] = "user0"
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(f"portfolio?username={username}")
    portfolio_list = [
        PortfolioInResponse(**portfolio) for portfolio in response.json()["data"]
    ]
    assert len(portfolio_list) == result


@pytest.mark.parametrize(
    "subscriber, username, result",
    [("", "", 6), ("user1", "user2", 5), ("wrong", "wrong", 0)],
)
async def test_get_portfolio_list_filtering_by_subscriber_or_username(
    authorized_client, fixture_db, portfolio_data_in_db, subscriber, username, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["username"] = "user2"
    for i in range(3):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["subscribers"] = ["user1"]
    for i in range(2):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["username"] = "user0"
    portfolio_data_in_db["subscribers"] = ["user0"]
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(
        f"portfolio?username={username}&subscriber={subscriber}"
    )
    portfolio_list = [
        PortfolioInResponse(**portfolio) for portfolio in response.json()["data"]
    ]
    assert len(portfolio_list) == result


@pytest.mark.parametrize(
    "fuzzy_query, result", [("", 6), ("portfolio", 5), ("0", 2), ("wrong", 0)]
)
async def test_get_portfolio_list_filtering_by_fuzzy_query(
    authorized_client, fixture_db, portfolio_data_in_db, fuzzy_query, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["name"] = f"p"
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    for i in range(3):
        portfolio_data_in_db["name"] = f"portfolio_{i}"
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    for i in range(2):
        portfolio_data_in_db["tags"] = [f"tag_{i}"]
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(f"portfolio?fuzzy_query={fuzzy_query}")
    portfolio_list = [
        PortfolioInResponse(**portfolio) for portfolio in response.json()["data"]
    ]
    assert len(portfolio_list) == result


@pytest.mark.parametrize(
    "status, result", [("", 3), ("running", 3), ("closed", 2), ("wrong", 0)]
)
async def test_get_portfolio_number_filtering_by_status(
    authorized_client, fixture_db, portfolio_data_in_db, status, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["status"] = "running"
    for i in range(3):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    portfolio_data_in_db["status"] = "closed"
    for i in range(2):
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(f"portfolio/number?status={status}")
    if result == 0:
        assert response.status_code == 422
    else:
        assert response.json() == result


@pytest.mark.parametrize(
    "fuzzy_query, result", [("", 6), ("portfolio", 5), ("0", 2), ("wrong", 0)]
)
async def test_get_portfolio_number_filtering_by_fuzzy_query(
    authorized_client, fixture_db, portfolio_data_in_db, fuzzy_query, result
):
    await delete_portfolio_many(fixture_db, {})
    portfolio_data_in_db["name"] = f"p"
    await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    for i in range(3):
        portfolio_data_in_db["name"] = f"portfolio_{i}"
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    for i in range(2):
        portfolio_data_in_db["tags"] = [f"tag_{i}"]
        await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(
        f"portfolio/number?fuzzy_query={fuzzy_query}"
    )
    assert response.json() == result


async def create_portfolio_assessment_time_series_data_with_portfolio(
    conn: AsyncIOMotorClient, portfolio: Portfolio
) -> Tuple[datetime, datetime, datetime]:
    """创建三个交易日的组合评估时点数据."""
    tdate = date2datetime()
    *_, day1, day2, day3 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )
    for index, day in enumerate([day1, day2, day3]):
        data = deepcopy(portfolio_assessment_time_series_data_in_db)
        data["trade_cost"] = index + 1
        data["winning_rate"] = index + 1
        data["portfolio"] = str(portfolio.id)
        data["tdate"] = day
        data_in_create = PortfolioAssessmentTimeSeriesDataInDB(**data)
        await create_portfolio_assessment_time_series_data(conn, data_in_create)
    return day1, day2, day3


@pytest.mark.parametrize("push_forward", ["true", "false"])
async def test_user_can_get_portfolio_yield_trend(
    authorized_client, portfolio_data_in_db, fixture_db, push_forward
):
    portfolio_data_in_db["category"] = PortfolioCategory.SimulatedTrading.value
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    (
        day1,
        day2,
        day3,
    ) = await create_portfolio_assessment_time_series_data_with_portfolio(
        fixture_db, portfolio
    )

    response = await authorized_client.get(
        f"portfolio/yield_trend/{portfolio.id}?push_forward={push_forward}&start_date={day2}&end_date={day3}"
    )
    data_list = [item["timestamp"] for item in response.json()["data_list"]]
    if push_forward == "true":
        except_timestamp = [day.strftime("%Y-%m-%d") for day in (day1, day2, day3)]
    else:
        except_timestamp = [day.strftime("%Y-%m-%d") for day in (day2, day3)]
    assert except_timestamp == data_list


async def test_user_can_get_portfolio_trade_stats(
    client, portfolio_data_in_db, fixture_db, fixture_settings, logined_vip_user
):
    portfolio_data_in_db["category"] = PortfolioCategory.SimulatedTrading.value
    portfolio_data_in_db["username"] = logined_vip_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    (
        day1,
        day2,
        day3,
    ) = await create_portfolio_assessment_time_series_data_with_portfolio(
        fixture_db, portfolio
    )

    client.headers = get_header(fixture_settings, logined_vip_user)
    response = await client.get(
        f"portfolio/trade_stats/{portfolio.id}?start_date={day2}&end_date={day2}"
    )
    portfolio_data = response.json()["portfolio_data"]
    # 由于day1, day2, day3的数据分别为1, 2, 3，所以当start_date和end_date为day2的话预期value应该为2
    for pd in portfolio_data:
        assert pd["value"] == 2


async def test_user_can_get_stock_stats(
    client,
    portfolio_data_in_db,
    fixture_db,
    fixture_settings,
    logined_vip_user,
    fund_account_position_data,
    fund_account_flow_list,
    portfolio_with_fund_account,
):
    portfolio, fund_account = portfolio_with_fund_account
    position = FundAccountPositionInDB(**fund_account_position_data)
    position.fund_id = str(fund_account.id)
    position.symbol = fund_account_flow_list[0].symbol
    await create_fund_account_position(fixture_db, position)

    for flow in fund_account_flow_list:
        flow.fund_id = str(fund_account.id)
        await create_fund_account_flow(fixture_db, flow)

    tdate = date2datetime()
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )
    client.headers = get_header(fixture_settings, logined_vip_user)
    response = await client.get(
        f"portfolio/stock_stats/{portfolio.id}?start_date={day3}&end_date={tdate}"
    )
    # 手动交易账户不显示当天数据
    assert not response.json()


async def test_user_can_get_assets(authorized_client, portfolio_with_fund_account):
    portfolio, fund_account = portfolio_with_fund_account
    response = await authorized_client.get(f"portfolio/account_asset/{portfolio.id}")
    assert float(fund_account.cash.to_decimal()) == response.json()["fund_available"]


@pytest.mark.parametrize("symbol, result", [("601816", "601816"), ("wrong", None)])
async def test_user_can_get_stock_position(
    authorized_client,
    fixture_db,
    fund_account_position_data,
    portfolio_with_fund_account,
    symbol,
    result,
):
    portfolio, fund_account = portfolio_with_fund_account
    fund_account_position_data["fund_id"] = str(fund_account.id)
    fund_account_position_data["symbol"] = "601816"
    await create_fund_account_position(
        fixture_db, FundAccountPositionInDB(**fund_account_position_data)
    )
    fund_account_position_data["symbol"] = "600519"
    await create_fund_account_position(
        fixture_db, FundAccountPositionInDB(**fund_account_position_data)
    )

    response = await authorized_client.get(
        f"portfolio/account_stock_position/{portfolio.id}?symbol={symbol}&exchange=1"
    )
    assert response.json().get("symbol") == result


async def test_user_can_get_target_data(
    authorized_client, portfolio_for_target_data: Portfolio
):
    code_list = [
        "10001",
        "10002",
        "10003",
        "10004",
        "10005",
        "10006",
        "10007",
        "10008",
        "10009",
        "100010",
        "100011",
        "100012",
        "100013",
        "100014",
    ]
    code_list_str = "&code_list=".join(code_list)
    response = await authorized_client.get(
        f"portfolio/target_data/{portfolio_for_target_data.id}?code_list={code_list_str}"
    )
    assert len(response.json()["data_list"]) == len(code_list)


async def test_user_can_get_basic_run_data(
    authorized_client, portfolio_with_fund_time_series_data
):
    portfolio, *_ = portfolio_with_fund_time_series_data
    response = await authorized_client.get(f"portfolio/basic_run_data/{portfolio.id}")
    assert (
        PortfolioBasicRunDataInResponse(**response.json()).portfolio.name
        == portfolio.name
    )


async def test_user_can_get_position(
    authorized_client,
    portfolio_with_fund_account,
    fixture_db,
    fund_account_position_data,
):
    portfolio, fund_account = portfolio_with_fund_account
    fund_account_position_data["fund_id"] = str(fund_account.id)
    await create_fund_account_position(
        fixture_db, FundAccountPositionInDB(**fund_account_position_data)
    )
    response = await authorized_client.get(f"portfolio/position/{portfolio.id}")
    response_json = response.json()
    assert response_json["portfolio"]["name"] == portfolio.name
    assert (
        response_json["industry_info"][0]["stocks"][0]["symbol"]
        == fund_account_position_data["symbol"]
    )


async def test_user_can_get_account_position_risk_level(
    mocker,
    authorized_client,
    portfolio_with_fund_account,
    fixture_db,
    fund_account_position_data,
    logined_vip_user,
):
    portfolio, fund_account = portfolio_with_fund_account
    fund_account_position_data["fund_id"] = str(fund_account.id)
    await create_fund_account_position(
        fixture_db, FundAccountPositionInDB(**fund_account_position_data)
    )
    mock_strategy_signal = mocker.patch(
        "app.service.portfolio.portfolio.get_strategy_signal",
        side_effect=mock_get_strategy_signal,
    )
    response = await authorized_client.get(
        f"portfolio/position/{portfolio.id}/risk_level"
    )
    tdate = (
        str_of_today()
        if FastTdate.is_tdate(str_of_today())
        else FastTdate.last_tdate(str_of_today())
    )
    if tdate == str_of_today() and datetime.now().hour < 19:
        tdate = FastTdate.last_tdate(tdate)
    mock_strategy_signal.assert_called_with(robot_test_data["风控装备列表"][0], tdate, tdate)
    response_json = response.json()[0]
    assert response_json["symbol"] == fund_account_position_data["symbol"]
    assert response_json["risk_level"]


async def test_user_can_get_risk_list(
    mocker,
    authorized_client,
    fund_account_position_data,
    fixture_db,
    portfolio_sci_risk_data,
    fund_account_data,
):
    fund_asset = await create_fund_account(
        fixture_db, FundAccountInDB(**fund_account_data)
    )
    portfolio_sci_risk_data["category"] = PortfolioCategory.ManualImport.value
    portfolio_sci_risk_data["name"] = get_random_str()
    portfolio_sci_risk_data["fund_account"][0]["fundid"] = str(fund_asset.id)
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_sci_risk_data))
    fund_account_position_data["fund_id"] = str(fund_asset.id)
    fund_account_position_data["symbol"] = "600100"
    await create_fund_account_position(
        fixture_db, FundAccountPositionInDB(**fund_account_position_data)
    )
    mock_strategy_signal = mocker.patch(
        "app.service.signal.get_strategy_signal",
        side_effect=mock_get_strategy_signal,
    )
    response = await authorized_client.get(f"portfolio/risk/{portfolio.id}")
    end_date = datetime.today().date()
    start_date = FastTdate.last_tdate(end_date)
    mock_strategy_signal.assert_called_with(
        robot_test_data["择时装备列表"][0],
        start_date.strftime("%Y%m%d"),
        end_date.strftime("%Y%m%d"),
    )
    response_json = response.json()[0]
    assert response_json["symbol"] == fund_account_position_data["symbol"]


async def test_user_can_update_risk_status(
    authorized_client,
    portfolio_sci_risk_data,
    fixture_db,
):
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_sci_risk_data))
    risk = portfolio_sci_risk_data["risks"][0]
    risk["id"] = str(risk["id"])
    risk["status"] = "31"
    response = await authorized_client.put(
        f"portfolio/risk/{portfolio.id}", json=[risk]
    )
    assert response.json()[0]["id"] == risk["id"]
    assert response.json()[0]["status"] == risk["status"]


async def test_user_can_delete_portfolio(
    client, fixture_db, portfolio_data_in_db, logged_in_root_user, fixture_settings
):
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    client.headers = get_header(fixture_settings, logged_in_root_user)
    response = await client.delete(f"portfolio/{portfolio.id}")
    assert response.json()["result"] == "success"


async def test_user_can_update_portfolio(
    authorized_client, portfolio_with_fund_account, portfolio_data_in_db
):
    portfolio, fund_account = portfolio_with_fund_account
    payload = {
        "portfolio": {
            "username": get_random_str(),
            "robot": portfolio.robot[::-1],
            "initial_funding": portfolio.initial_funding,
            "close_date": str(portfolio.close_date),
            "fund_account": [
                {"userid": get_random_str(), "fundid": str(fund_account.id)}
            ],
        }
    }
    response = await authorized_client.put(f"portfolio/{portfolio.id}", json=payload)
    assert response.json()["matched_count"] == 1
    assert response.json()["modified_count"] == 1


async def test_user_can_partial_update_portfolio(
    authorized_client, portfolio_with_fund_account
):
    portfolio, _ = portfolio_with_fund_account

    payload = {
        "portfolio": {
            "tags": ["tag1", "tag2"],
            "robot": portfolio.robot[::-1],
        }
    }
    response = await authorized_client.patch(f"portfolio/{portfolio.id}", json=payload)
    assert response.json()["matched_count"] == 1
    assert response.json()["modified_count"] == 1


async def test_user_can_get_portfolio(
    authorized_client, portfolio_data_in_db, fixture_db
):
    portfolio_data_in_db["name"] = get_random_str()
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    response = await authorized_client.get(f"portfolio/{portfolio.id}")
    assert response.json()["name"] == portfolio.name


async def test_user_can_get_all_position(
    client,
    portfolio_data_in_db,
    fixture_db,
    fund_account_data,
    logined_vip_user,
    fund_account_position_data,
    fixture_settings,
):
    fund_asset = await create_fund_account(
        fixture_db, FundAccountInDB(**fund_account_data)
    )
    portfolio_data_in_db["category"] = PortfolioCategory.ManualImport.value
    portfolio_data_in_db["name"] = get_random_str()
    portfolio_data_in_db["fund_account"][0]["fundid"] = str(fund_asset.id)
    portfolio_data_in_db["username"] = logined_vip_user["user"]["username"]
    portfolio = await create_portfolio(fixture_db, Portfolio(**portfolio_data_in_db))
    fund_account_position_data["fund_id"] = str(fund_asset.id)
    await create_fund_account_position(
        fixture_db, FundAccountPositionInDB(**fund_account_position_data)
    )
    client.headers = get_header(fixture_settings, logined_vip_user)
    response = await client.get(f"portfolio/position/")
    response_json = [x for x in response.json() if x["id"] == str(portfolio.id)][0]
    assert (
        response_json["position"][0]["symbol"] == fund_account_position_data["symbol"]
    )
