from copy import deepcopy

import pytest

from app.models.fund_account import FundAccountFlowInDB, FundAccountInDB
from app.models.rwmodel import PyDecimal, PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.portfolio import PortfolioInResponse

pytestmark = pytest.mark.asyncio


def test_create_fund_account_flow_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    mocker,
    fund_account_data,
    fund_account_flow_data,
    fund_account_flow_in_db,
):
    async def fake_get_fund_account_by_id(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_by_id",
        side_effect=fake_get_fund_account_by_id,
    )

    async def coro(*args, **kwargs):
        return fund_account_flow_in_db

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.flow_validation", side_effect=coro
    )
    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.user_validation",
        side_effect=coro,
    )
    flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.calculate_flow_fee",
        return_value=fund_account_flow_in_db,
    )
    update_position = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_position_by_flow",
        side_effect=coro,
    )
    create = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.create_fund_account_flow",
        side_effect=coro,
    )
    update_account = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_fund_account_by_flow",
        side_effect=coro,
    )
    set_import_date = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.set_portfolio_import_date",
        side_effect=coro,
    )
    fund_account_flow_data["ttype"] = "3"
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/fund_account/flow/",
        json=fund_account_flow_data,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert flow.called
    assert update_position.called
    assert create.called
    assert update_account.called
    assert set_import_date.called


def test_update_fund_account_flow_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fund_account_flow_data,
    fund_account_data,
    mocker,
):
    async def coro(*args, **kwargs):
        return UpdateResult(matched_count=1, modified_count=1)

    async def fake_flow(*args, **kwargs):
        return FundAccountFlowInDB(**fund_account_flow_data)

    async def fake_get_fund_account_by_id(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.user_validation",
        side_effect=coro,
    )
    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_by_id",
        side_effect=fake_get_fund_account_by_id,
    )
    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.flow_validation", side_effect=coro
    )
    get_flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_flow_by_id",
        side_effect=fake_flow,
    )
    cal_flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.calculate_flow_fee",
        return_value=FundAccountFlowInDB(**fund_account_flow_data, ttype="3"),
    )
    update_position = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_position_by_flow",
        side_effect=coro,
    )
    update_account_flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_fund_account_flow_by_id",
        side_effect=coro,
    )
    update_account = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_fund_account_by_flow",
        side_effect=coro,
    )
    fund_account_flow_data["ttype"] = "3"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/fund_account/flow/60122d282c27e2a494940a36",
        json=fund_account_flow_data,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert get_flow.called
    assert cal_flow.called
    assert update_position.called
    assert update_account_flow.called
    assert update_account.called


def test_delete_fund_account_flow_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fund_account_data,
    mocker,
    fund_account_flow_data
):
    async def fake_get_fund_account_by_id(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_by_id",
        side_effect=fake_get_fund_account_by_id,
    )

    async def coro(*args, **kwargs):
        return ResultInResponse()

    async def fake_fund_account_flow(*args, **kwargs):
        flow = deepcopy(fund_account_flow_data)
        flow["fundeffect"] = PyDecimal("10")
        flow["stkeffect"] = 10
        flow["fund_id"] = "607799f381a6ac32588fbe08"
        flow["ttype"] = "3"
        return FundAccountFlowInDB(**flow)

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.user_validation",
        side_effect=coro,
    )
    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.position_validation_delete",
        side_effect=coro,
    )
    flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_flow_by_id",
        side_effect=fake_fund_account_flow,
    )
    update_position = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_position_by_flow",
        side_effect=coro,
    )
    update_account = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_fund_account_by_flow",
        side_effect=coro,
    )
    delete_flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.delete_fund_account_flow_by_id",
        side_effect=coro,
    )
    set_import_date = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.set_portfolio_import_date",
        side_effect=coro,
    )
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/fund_account/flow/60122d282c27e2a494940a36",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert flow.called
    assert update_position.called
    assert update_account.called
    assert delete_flow.called
    assert set_import_date.called


def test_get_fund_account_flow_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    mocker,
    fund_account_flow_in_db,
    portfolio_data_in_db,
):
    async def fake_get_portfolio_by_id(*args, **kwargs):
        return PortfolioInResponse(**portfolio_data_in_db)

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_portfolio_by_id",
        side_effect=fake_get_portfolio_by_id,
    )

    async def coro(*args, **kwargs):
        return [fund_account_flow_in_db]

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.user_validation",
        side_effect=coro,
    )
    get_flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_flow", side_effect=coro
    )
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/fund_account/flow/?portfolio_id={PyObjectId()}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert get_flow.called


@pytest.fixture
def deposit_or_withdraw():
    json = {
        "fund_id": "60122d282c27e2a494940a36",
        "amount": "10000",
        "tdate": "2021-03-30",
    }
    return json


def test_deposit_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    mocker,
    deposit_or_withdraw,
    fund_account_flow_in_db,
    fund_account_data,
):
    async def coro(*args, **kwargs):
        return fund_account_flow_in_db

    async def fake_get_fund_account_by_id(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.user_validation",
        side_effect=coro,
    )
    fund_account = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_by_id",
        side_effect=fake_get_fund_account_by_id,
    )
    update_account = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_fund_account_by_flow",
        side_effect=coro,
    )
    create_flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.create_fund_account_flow",
        side_effect=coro,
    )
    set_import_date = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.set_portfolio_import_date",
        side_effect=coro,
    )
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/fund_account/deposit",
        json=deposit_or_withdraw,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert fund_account.called
    assert update_account.called
    assert create_flow.called
    assert set_import_date.called


def test_withdraw_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    mocker,
    deposit_or_withdraw,
    fund_account_flow_in_db,
    fund_account_data,
):
    async def coro(*args, **kwargs):
        return fund_account_flow_in_db

    async def fake_get_fund_account_by_id(*args, **kwargs):
        return FundAccountInDB(**fund_account_data)

    fund_account = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.get_fund_account_by_id",
        side_effect=fake_get_fund_account_by_id,
    )
    mocker.patch(
        "app.api.api_v1.endpoints.fund_account.user_validation",
        side_effect=coro,
    )
    update_account = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.update_fund_account_by_flow",
        side_effect=coro,
    )
    create_flow = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.create_fund_account_flow",
        side_effect=coro,
    )
    set_import_date = mocker.patch(
        "app.api.api_v1.endpoints.fund_account.set_portfolio_import_date",
        side_effect=coro,
    )
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/fund_account/withdraw",
        json=deposit_or_withdraw,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert fund_account.called
    assert update_account.called
    assert create_flow.called
    assert set_import_date.called
