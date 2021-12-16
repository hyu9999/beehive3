from copy import deepcopy
from datetime import timedelta, datetime

import pytest
from fastapi import HTTPException
from stralib import FastTdate

from app.crud.fund_account import create_fund_account, create_fund_account_flow
from app.enums.fund_account import FlowTType
from app.models.fund_account import FundAccountFlowInDB, FundAccountInDB
from app.models.rwmodel import PyDecimal
from app.schema.fund_account import DepositOrWithDraw, FundAccountFlowInCreate
from app.service.datetime import get_early_morning
from app.service.fund_account.validator import (
    capital_validation,
    flow_validation,
    position_validation,
    withdraw_validation,
    date_validation,
    position_validation_delete, ttype_validation,
)
from tests.test_helper import get_random_str

pytestmark = pytest.mark.asyncio


async def test_flow_validation(fixture_db, fund_account_flow_data):
    fund_account_flow_data["tdate"] = "2021-04-14"
    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype="3")
    await flow_validation(flow)
    fund_account_flow_data["tdate"] = "2021-04-11"
    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype="3")
    with pytest.raises(HTTPException):
        await flow_validation(flow)
    fund_account_flow_data["tdate"] = "2021-04-14"
    fund_account_flow_data["stkeffect"] = 99
    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype="3")
    with pytest.raises(HTTPException):
        await flow_validation(flow)


def test_ttype_validation(fund_account_flow_data):
    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype="3")
    ttype_validation(flow)
    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype="5")
    with pytest.raises(HTTPException):
        ttype_validation(flow)
    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype="6")
    with pytest.raises(HTTPException):
        ttype_validation(flow)


def test_capital_validation(fund_account_data, fund_account_flow_data):
    fund_account = FundAccountInDB(**fund_account_data)
    flow = FundAccountFlowInDB(**fund_account_flow_data, ttype="3")
    capital_validation(fund_account, flow)
    fund_account.cash = PyDecimal("0")
    with pytest.raises(HTTPException):
        capital_validation(fund_account, flow)


async def test_position_validation_with_buy(
    fixture_db,
    fund_account_flow_list,
):
    fund_id = get_random_str()
    fund_account_flow_list = deepcopy(fund_account_flow_list)
    for flow in fund_account_flow_list:
        flow.fund_id = fund_id
        await create_fund_account_flow(fixture_db, flow)
    flow = fund_account_flow_list[1]
    flow.ttype = FlowTType.BUY
    flow.fund_id = fund_id
    await position_validation(fixture_db, flow)


async def test_position_validation_delete(
    fixture_db,
    portfolio_with_position,
    fund_account_flow_data
):
    portfolio, fund_asset, position_list = portfolio_with_position
    flow = FundAccountFlowInDB(**fund_account_flow_data, ttype=FlowTType.BUY)
    flow.fund_id = str(fund_asset.id)
    flow.symbol = "000000"
    with pytest.raises(HTTPException):
        await position_validation_delete(fixture_db, flow)
    flow.symbol = position_list[-1].symbol
    flow.stkeffect = position_list[-1].volume + 1
    with pytest.raises(HTTPException):
        await position_validation_delete(fixture_db, flow)
    flow.stkeffect = position_list[-1].volume
    await position_validation_delete(fixture_db, flow)


async def test_position_validation_with_no_position(
    fixture_db,
    fund_account_flow_list,
):
    flow = fund_account_flow_list[1]
    flow.ttype = FlowTType.SELL
    flow.fund_id = get_random_str()
    with pytest.raises(HTTPException):
        await position_validation(fixture_db, flow)


async def test_position_validation_with_position_short(
    fixture_db,
    fund_account_flow_list,
):
    fund_id = get_random_str()
    fund_account_flow_list = deepcopy(fund_account_flow_list)
    for flow in fund_account_flow_list:
        flow.fund_id = fund_id
        await create_fund_account_flow(fixture_db, flow)
    flow = fund_account_flow_list[1]
    flow.ttype = FlowTType.SELL
    await position_validation(fixture_db, flow)
    flow.stkeffect = -6000
    with pytest.raises(HTTPException):
        await position_validation(fixture_db, flow)


async def test_withdraw_validation(
    fixture_db, fund_account_data, fund_account_flow_list
):
    tdate = get_early_morning()
    *_, day1, day2, day3, day4 = FastTdate.query_all_tdates(
        tdate - timedelta(days=100), tdate
    )
    fund_account = await create_fund_account(
        fixture_db, FundAccountInDB(**fund_account_data)
    )
    fund_account_flow_list = deepcopy(fund_account_flow_list)
    for flow in fund_account_flow_list:
        flow.fund_id = str(fund_account.id)
        await create_fund_account_flow(fixture_db, flow)
    flow = DepositOrWithDraw(
        fund_id=str(fund_account.id), amount=500000, tdate=tdate.date()
    )
    await withdraw_validation(fixture_db, flow, fund_account)
    with pytest.raises(HTTPException):
        flow.amount = PyDecimal("950000")
        await withdraw_validation(fixture_db, flow, fund_account)
    with pytest.raises(HTTPException):
        flow.amount = PyDecimal("910000")
        flow.tdate = day2
        await withdraw_validation(fixture_db, flow, fund_account)


async def test_date_validation(fund_account_flow_data):
    flow = FundAccountFlowInCreate(**fund_account_flow_data, ttype="3")
    date_validation(flow)
    flow.tdate = datetime(2017, 1, 1)
    with pytest.raises(HTTPException):
        date_validation(flow)
