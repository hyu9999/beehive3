from datetime import datetime, time
from typing import Union

from fastapi import HTTPException
from hq2redis import HQSourceError
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app.crud.fund_account import (
    get_fund_account_flow_from_db,
    get_fund_account_position_from_db,
)
from app.crud.portfolio import get_portfolio_list
from app.enums.fund_account import FlowTType
from app.enums.portfolio import 组合状态
from app.models.fund_account import FundAccountFlowInDB, FundAccountInDB
from app.outer_sys.hq import get_security_meta
from app.schema.fund_account import (
    DepositOrWithDraw,
    FundAccountFlowInCreate,
    FundAccountFlowInUpdate,
)
from app.schema.user import User
from app.utils.datetime import date2datetime
from app.utils.exchange import convert_exchange


def time_validation():
    if time(21) < time() < time(23, 59):
        raise HTTPException(400, detail=f"交易日21~24点为系统数据清算时间，禁止操作数据。")


def tdate_validation(flow: DepositOrWithDraw):
    if not FastTdate.is_tdate(flow.tdate):
        raise HTTPException(400, detail=f"非交易日无法出入金。")


def ttype_validation(flow: FundAccountFlowInCreate):
    if flow.ttype in [FlowTType.DIVIDEND, FlowTType.TAX]:
        raise HTTPException(400, detail=f"无法对分红和扣税流水进行操作。")


def date_validation(flow: Union[FundAccountFlowInCreate, DepositOrWithDraw]):
    limit_date = datetime(2018, 1, 1)
    if date2datetime(flow.tdate) < limit_date:
        if isinstance(flow, FundAccountFlowInCreate):
            raise HTTPException(400, detail=f"无法创建时间早于{limit_date.date()}的调仓记录。")
        if isinstance(flow, DepositOrWithDraw):
            raise HTTPException(400, detail=f"无法创建时间早于{limit_date.date()}的出入金记录。")


async def user_validation(conn: AsyncIOMotorClient, user: User, fund_id: str) -> None:
    portfolio_list = await get_portfolio_list(
        conn, {"username": user.username, "status": 组合状态.running}
    )
    fund_id_list = []
    for portfolio in portfolio_list:
        for fund_account in portfolio.fund_account:
            fund_id_list.append(fund_account.fundid)
    if fund_id not in fund_id_list:
        raise HTTPException(400, detail=f"无法对他人的组合进行操作。")


def pre_flow_validation(
    flow: Union[FundAccountFlowInCreate, FundAccountFlowInUpdate]
) -> None:
    if flow.cost.to_decimal() <= 0:
        raise HTTPException(400, detail=f"流水成本价不能小于等于0。")
    if flow.stkeffect <= 0:
        raise HTTPException(400, detail=f"流水成交数量不能小于等于0。")


async def flow_validation(
    flow: Union[FundAccountFlowInCreate, FundAccountFlowInUpdate]
) -> None:
    if isinstance(flow, FundAccountFlowInCreate):
        if not FastTdate.is_tdate(flow.tdate):
            raise HTTPException(400, detail=f"‘{flow.tdate}’不是交易日。")
        try:
            security = await get_security_meta(
                flow.symbol, convert_exchange(flow.exchange, to="beehive")
            )
        except HQSourceError:
            raise HTTPException(400, detail=f"未找到证券‘{flow.symbol}.{flow.exchange}’。")
        if flow.ttype == FlowTType.BUY and abs(flow.stkeffect) % security.min_unit != 0:
            raise HTTPException(
                400,
                detail=f"成交量填写错误，该证券的成交量应为‘{security.min_unit}’的倍数。",
            )
    if flow.ttype not in [FlowTType.BUY, FlowTType.SELL]:
        raise HTTPException(400, detail=f"流水水类型错误。")


def capital_validation(
    fund_account: FundAccountInDB, flow: FundAccountFlowInDB
) -> None:
    """用户资金验证."""
    if fund_account.cash.to_decimal() + flow.fundeffect.to_decimal() <= 0:
        raise HTTPException(400, detail=f"用户可用金额不足。")


async def position_validation(
    conn: AsyncIOMotorClient, flow: FundAccountFlowInDB
) -> None:
    """持仓验证."""
    if flow.ttype == FlowTType.SELL:
        flow_list = await get_fund_account_flow_from_db(
            conn, fund_id=flow.fund_id, symbol=flow.symbol, end_date=flow.tdate
        )
        if not flow_list:
            raise HTTPException(
                400,
                detail=f"交易日‘{flow.tdate.date()}`未找到证券‘{flow.symbol}’的可用持仓，无法卖出该证券。",
            )
        abs_stkeffect = sum([flow.stkeffect for flow in flow_list])
        if abs_stkeffect < abs(flow.stkeffect):
            raise HTTPException(
                400, detail=f"交易日‘{flow.tdate.date()}`证券‘{flow.symbol}’可用持仓不足，无法卖出该证券。"
            )


async def position_validation_delete(
    conn: AsyncIOMotorClient, flow: FundAccountFlowInDB
) -> None:
    """删除时候的持仓验证."""
    if flow.ttype == FlowTType.BUY:
        position = await get_fund_account_position_from_db(
            conn, fund_id=flow.fund_id, symbol=flow.symbol, exchange=flow.exchange
        )
        if not position:
            raise HTTPException(400, detail="无法删除该买单，账户可用持仓不足。")
        position = position[0]
        if abs(flow.stkeffect) > position.volume:
            raise HTTPException(400, detail="无法删除该买单，账户可用持仓不足。")


async def withdraw_validation(
    conn: AsyncIOMotorClient, flow: DepositOrWithDraw, fund_account: FundAccountInDB
) -> None:
    """出金验证."""
    flow_list = await get_fund_account_flow_from_db(
        conn, fund_id=flow.fund_id, end_date=flow.tdate
    )
    abs_fundeffect = sum([flow.fundeffect.to_decimal() for flow in flow_list] or [])
    if (
        abs(flow.amount.to_decimal())
        > abs_fundeffect + fund_account.capital.to_decimal()
    ):
        raise HTTPException(400, detail=f"交易日‘{flow.tdate}’用户可用资金不足。")
