from decimal import Decimal

import pytest
from bson import Decimal128, ObjectId

from app.enums.fund_account import Exchange, FlowTType, CurrencyType
from app.models.fund_account import FundAccountPositionInDB, FundAccountInDB
from app.service.time_series_data.converter import field_converter, position2time_series, fund2time_series, \
    position_time_series_data2ability, fund_time_series_data2ability, ability2fund_time_series_data, \
    ability2position_time_series_data, pt_flow2beehive_flow
from app.utils.datetime import date2datetime

pytestmark = pytest.mark.asyncio


def test_field_converter():
    d = {
        "decimal128": Decimal128("10"),
        "exchange": Exchange.CNSESZ,
        "flowttype": FlowTType.BUY,
        "currency": CurrencyType.CNY,
        "objectid": ObjectId()
    }
    result = field_converter(d)
    assert isinstance(result["decimal128"], float)
    assert isinstance(result["exchange"], str)
    assert isinstance(result["flowttype"], str)
    assert isinstance(result["currency"], str)
    assert isinstance(result["objectid"], str)


async def test_position2time_series(
    fund_account_position_data,
    mocker,
):
    fund_account_position = FundAccountPositionInDB(**fund_account_position_data)

    async def fake_get_security_price(*args, **kwargs):
        class Security:
            current = Decimal("10")
        return Security()

    mocker.patch("app.service.time_series_data.converter.get_security_price", fake_get_security_price)
    await position2time_series(
        [fund_account_position], fund_account_position_data["fund_id"], date2datetime()
    )


def test_fund2time_series(fund_account_data):
    fund_account = FundAccountInDB(**fund_account_data)
    fund2time_series(fund_account, date2datetime())


def test_position_time_series_data2ability(
    position_time_series_data_list
):
    position_time_series_data2ability(position_time_series_data_list[0])


def test_fund_time_series_data2ability(
    fund_time_series_data_list
):
    fund_time_series_data2ability(fund_time_series_data_list[0])


def test_ability2fund_time_series_data():
    ability_dict = {
        date2datetime(): {
            "fund_id": "60122d282c27e2a494940a36",
            "fund_balance": "100000",
            "market_value": "100000"
        }
    }
    ability2fund_time_series_data(ability_dict)


def test_ability2position_time_series_data():
    ability_dict = {
        date2datetime(): {
            "600519": [{
                "exchange": "CNSESH",
                "stock_quantity": "1000",
                "market_value": "100000",
                "buy_date": date2datetime()
            }]
        }
    }
    ability2position_time_series_data("60122d282c27e2a494940a36", ability_dict)


def test_pt_flow2beehive_flow():
    flow_json = {
        "_id": "5fb5cc67d0510b5dd44b214f",
        "symbol": "600837",
        "exchange": "SH",
        "entrust_id": "5fb5cc67d0510b5dd44b214b",
        "user": "5face26c57fbb548227231d5",
        "trade_category": "buy",
        "volume": 1000,
        "sold_price": "14.0",
        "amount": "-14006.0000",
        "costs": {
            "total": "6.0000",
            "commission": "6.0000",
            "tax": "0"
        },
        "deal_time": date2datetime(),
    }
    pt_flow2beehive_flow(flow_json, CurrencyType.CNY)
    flow_json["deal_time"] = "2020-11-20T09:13:58.073+0000"
    pt_flow2beehive_flow(flow_json, CurrencyType.CNY)
