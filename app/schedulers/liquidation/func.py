import asyncio
import time as t
from dataclasses import asdict
from datetime import time
from decimal import Decimal
from typing import List

from dividend_utils.dividend import get_xdr_price
from dividend_utils.liquidator import liquidate_dividend, liquidate_dividend_tax
from dividend_utils.models import Flow, Position
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app.crud.fund_account import (
    create_fund_account_flow,
    delete_fund_account_flow_many,
    get_fund_account_by_id,
    get_fund_account_flow_from_db,
    get_fund_account_position_from_db,
    update_fund_account_by_id,
    update_fund_account_position_by_id,
)
from app.crud.portfolio import get_portfolio_list
from app.crud.time_series_data import get_position_time_series_data
from app.db.mongodb import db
from app.enums.fund_account import FlowTType
from app.enums.portfolio import PortfolioCategory, 组合状态
from app.global_var import G
from app.models.base.time_series_data import Position as TSPosition
from app.models.base.time_series_data import Position as TimeSeriesPosition
from app.models.fund_account import (
    FundAccountFlowInDB,
    FundAccountInDB,
    FundAccountPositionInDB,
)
from app.models.rwmodel import PyDecimal, PyObjectId
from app.models.time_series_data import PositionTimeSeriesDataInDB
from app.schema.fund_account import FundAccountInUpdate, FundAccountPositionInUpdate
from app.service.check_status import CheckStatus
from app.service.datetime import get_early_morning, str_of_today
from app.service.fund_account.fund_account import liquidation_fund_asset
from app.utils.datetime import date2datetime, get_seconds


def time_series_position2dividend(
    fund_id: str, position: TimeSeriesPosition
) -> Position:
    return Position(
        fund_id=fund_id,
        symbol=position.symbol,
        exchange=position.market,
        volume=position.stkbal,
    )


def reverse_flow(flow: FundAccountFlowInDB) -> FundAccountFlowInDB:
    """调转flow"""
    flow.fundeffect = PyDecimal(-flow.fundeffect.to_decimal())
    flow.stkeffect = -flow.stkeffect
    return flow


def make_ts_position(flow: FundAccountFlowInDB) -> TSPosition:
    return TSPosition(
        symbol=flow.symbol,
        market=flow.exchange,
        stkbal=flow.stkeffect,
        mktval=PyDecimal("0"),
    )


def update_time_series_position_data_by_flow(
    time_series_position_data: List[PositionTimeSeriesDataInDB],
    flow: FundAccountFlowInDB,
) -> None:
    """添加分红流水到持仓时点数据."""
    for ts_position in filter(
        lambda ts: ts.tdate >= flow.tdate, time_series_position_data
    ):
        position = next(
            filter(lambda p: p.symbol == flow.symbol, ts_position.position_list), None
        )
        if position is not None:
            position.stkbal += flow.stkeffect
        else:
            ts_position.position_list.append(make_ts_position(flow))


async def liquidate_dividend_task():
    """清算分红（手动调仓组合）."""
    from zvt.api import DividendDetail

    if not FastTdate.is_tdate():
        return None
    # 等待时点数据同步完成
    while not await CheckStatus.check_time_series_status():
        await asyncio.sleep(10)

    portfolio_list = await get_portfolio_list(
        db.client, {"status": 组合状态.running, "category": PortfolioCategory.ManualImport}
    )
    tdate = get_early_morning()
    for portfolio in portfolio_list:
        fund_account = portfolio.fund_account[0]
        fund_asset = await get_fund_account_by_id(
            db.client, PyObjectId(fund_account.fundid)
        )
        start_date = FastTdate.next_tdate(fund_asset.ts_data_sync_date)

        # 持仓时点数据
        position_time_series_data = await get_position_time_series_data(
            db.client, fund_id=fund_account.fundid, start_date=start_date.date()
        )

        if start_date != tdate:
            # 处理已失效的分红流水
            dividend_flow_list = await get_fund_account_flow_from_db(
                db.client,
                fund_id=fund_account.fundid,
                start_date=start_date.date(),
                ttype=[FlowTType.DIVIDEND],
            )
            flow_tdates = []
            for flow in dividend_flow_list:
                update_cost = False
                if flow.tdate not in flow_tdates:
                    flow_tdates.append(flow.tdate)
                    update_cost = True
                flow = reverse_flow(flow)
                position = await get_fund_account_position_from_db(
                    db.client, fund_id=flow.fund_id, symbol=flow.symbol
                )
                if position:
                    await update_position_by_flow(
                        db.client, position[0], flow, update_cost
                    )
                if flow.stkeffect != 0:
                    update_time_series_position_data_by_flow(
                        position_time_series_data, flow
                    )
            total_dividend = sum(
                [
                    flow.fundeffect.to_decimal()
                    for flow in dividend_flow_list
                    if flow.stkeffect == 0
                ]
                or [Decimal("0")]
            )
            if total_dividend != Decimal("0"):
                await update_fund_account_by_flow(db.client, fund_asset, total_dividend)

            # 删除已有分红流水
            await delete_fund_account_flow_many(
                db.client,
                {"_id": {"$in": [flow.id for flow in dividend_flow_list]}},
            )

        while position_time_series_data:
            position_tdate = position_time_series_data.pop(0)
            liq_date = position_tdate.tdate
            if position_tdate.position_list is None:
                continue
            for position in position_tdate.position_list:
                dividend_detail = DividendDetail.query_data(
                    filters=[DividendDetail.code == position.symbol]
                )
                dividend_flow_list = liquidate_dividend(
                    dividend_detail,
                    time_series_position2dividend(fund_account.fundid, position),
                    liq_date,
                )
                if dividend_flow_list:
                    flow_list_in_db = [
                        FundAccountFlowInDB(**asdict(dividend_flow))
                        for dividend_flow in dividend_flow_list
                    ]
                    for flow_in_db in flow_list_in_db:
                        await create_fund_account_flow(db.client, flow_in_db)
                        if flow_in_db.tdate <= tdate and flow_in_db.stkeffect:
                            update_time_series_position_data_by_flow(
                                position_time_series_data, flow_in_db
                            )

    redis_key = f"{str_of_today()}_liquidate_dividend"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(23, 59)))


async def update_fund_account_by_flow(
    conn: AsyncIOMotorClient, fund_account: FundAccountInDB, total_dividend: Decimal
) -> None:
    """通过分红流水更新资金账户资产."""
    fund_account_in_update = FundAccountInUpdate(**fund_account.dict())
    fund_account_in_update.cash = PyDecimal(
        fund_account.cash.to_decimal() + total_dividend
    )
    fund_account_in_update.assets = PyDecimal(
        fund_account.assets.to_decimal() + total_dividend
    )
    await update_fund_account_by_id(conn, fund_account.id, fund_account_in_update)


async def update_position_by_flow(
    conn: AsyncIOMotorClient,
    position: FundAccountPositionInDB,
    flow: FundAccountFlowInDB,
    update_cost: bool = True,
):
    """通过分红流水更新持仓."""
    from zvt.api import DividendDetail

    position.volume += flow.stkeffect
    position.available_volume = position.volume
    if update_cost:
        # 更新成本价
        dividend_detail = DividendDetail.query_data(
            filters=[
                DividendDetail.code == position.symbol,
                DividendDetail.dividend_pay_date == flow.tdate.date(),
            ]
        )
        xdr_cost = get_xdr_price(dividend_detail, float(position.cost.to_decimal()))
        if flow.stkeffect < 0 or flow.fundeffect.to_decimal() < 0:
            xdr_price = position.cost.to_decimal() - Decimal(str(xdr_cost))
            xdr_cost = position.cost.to_decimal() + xdr_price
        position.cost = PyDecimal(str(xdr_cost))
    position_in_update = FundAccountPositionInUpdate(**position.dict())
    await update_fund_account_position_by_id(conn, position.id, position_in_update)


async def liquidate_dividend_flow_task():
    """清算分红流水（手动调仓组合）."""
    if not FastTdate.is_tdate():
        return None
    while not await CheckStatus.check_liquidate_dividend_status():
        await asyncio.sleep(10)

    portfolio_list = await get_portfolio_list(
        db.client, {"status": 组合状态.running, "category": PortfolioCategory.ManualImport}
    )
    tdate = get_early_morning()
    for portfolio in portfolio_list:
        fund_account = portfolio.fund_account[0]
        fund_asset = await get_fund_account_by_id(
            db.client, PyObjectId(fund_account.fundid)
        )
        start_date = FastTdate.next_tdate(fund_asset.ts_data_sync_date)
        flow_list = await get_fund_account_flow_from_db(
            db.client,
            fund_id=fund_account.fundid,
            start_date=start_date.date(),
            end_date=tdate.date(),
            ttype=[FlowTType.DIVIDEND],
        )
        tdate_list = []
        for flow in flow_list:
            update_cost = False
            if flow.tdate not in tdate_list:
                tdate_list.append(flow.tdate)
                update_cost = True
            position = await get_fund_account_position_from_db(
                db.client, fund_id=flow.fund_id, symbol=flow.symbol
            )
            if position:
                await update_position_by_flow(db.client, position[0], flow, update_cost)
        total_dividend = sum(
            [flow.fundeffect.to_decimal() for flow in flow_list if flow.stkeffect == 0]
            or [Decimal("0")]
        )
        if total_dividend != Decimal("0"):
            await update_fund_account_by_flow(db.client, fund_asset, total_dividend)
        await liquidation_fund_asset(db.client, portfolio)
    redis_key = f"{str_of_today()}_liquidate_dividend_flow"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(23, 59)))


def beehiveflow2dividend(flow_list: List[FundAccountFlowInDB]) -> List[Flow]:
    dividend_flow_list = []
    for index, flow in enumerate(flow_list):
        flow_dict = flow.dict()
        flow_dict["ts"] = t.mktime(flow.tdate.timetuple()) + index
        flow_dict["tdate"] = flow.tdate.date()
        dividend_flow_list.append(Flow(**flow_dict))
    return dividend_flow_list


async def liquidate_dividend_tax_task():
    """清算红利税（手动调仓组合）."""
    from zvt.api import DividendDetail

    if not FastTdate.is_tdate():
        return None
    while not await CheckStatus.check_liquidate_dividend_flow_status():
        await asyncio.sleep(10)
    portfolio_list = await get_portfolio_list(
        db.client, {"status": 组合状态.running, "category": PortfolioCategory.ManualImport}
    )
    for portfolio in portfolio_list:
        fund_account = portfolio.fund_account[0]
        fund_asset = await get_fund_account_by_id(
            db.client, PyObjectId(fund_account.fundid)
        )
        start_date = FastTdate.next_tdate(fund_asset.ts_data_sync_date)
        flow_list = await get_fund_account_flow_from_db(
            db.client,
            fund_id=fund_account.fundid,
            start_date=start_date.date(),
            ttype=[FlowTType.TAX],
        )
        for flow in flow_list:
            position = await get_fund_account_position_from_db(
                db.client, fund_id=flow.fund_id, symbol=flow.symbol
            )
            if position:
                position = position[0]
                tax_cost = abs(flow.fundeffect.to_decimal()) / position.volume
                position.cost = PyDecimal(position.cost.to_decimal() - tax_cost)
                position_in_update = FundAccountPositionInUpdate(**position.dict())
                await update_fund_account_position_by_id(
                    db.client, position.id, position_in_update
                )
        total_dividend = sum(
            [flow.fundeffect.to_decimal() for flow in flow_list if flow.stkeffect == 0]
            or [Decimal("0")]
        )
        if total_dividend != Decimal("0"):
            await update_fund_account_by_flow(db.client, fund_asset, total_dividend)
        # 删除已有扣税流水
        await delete_fund_account_flow_many(
            db.client,
            {
                "fund_id": fund_account.fundid,
                "ttype": "6",
                "tdate": {"$gte": start_date},
            },
        )
        flow_list = await get_fund_account_flow_from_db(
            db.client,
            fund_id=fund_account.fundid,
            ttype=[FlowTType.SELL, FlowTType.BUY],
        )
        flow_list = beehiveflow2dividend(flow_list)
        tax_flow_list = []
        for order in filter(
            lambda f: f.ttype == FlowTType.SELL and f.tdate >= start_date.date(),
            flow_list,
        ):
            dividend_detail = DividendDetail.query_data(
                filters=[
                    DividendDetail.code == order.symbol,
                    DividendDetail.record_date < date2datetime(order.tdate),
                ]
            )
            symbol_flow_list = list(
                filter(lambda f: f.symbol == order.symbol, flow_list)
            )
            if not flow_list:
                continue
            tax_flow = liquidate_dividend_tax(
                dividend_detail,
                order,
                symbol_flow_list,
            )
            if tax_flow:
                flow = FundAccountFlowInDB(**asdict(tax_flow))
                flow_in_db = await create_fund_account_flow(db.client, flow)
                tax_flow_list.append(flow_in_db)
        fund_asset = await get_fund_account_by_id(
            db.client, PyObjectId(fund_account.fundid)
        )
        total_dividend = sum(
            [flow.fundeffect.to_decimal() for flow in tax_flow_list] or [Decimal("0")]
        )
        if total_dividend != Decimal("0"):
            await update_fund_account_by_flow(db.client, fund_asset, total_dividend)
        for tax_flow in tax_flow_list:
            position = await get_fund_account_position_from_db(
                db.client, fund_id=fund_account.fundid, symbol=tax_flow.symbol
            )
            if position:
                position = position[0]
                tax_cost = abs(tax_flow.fundeffect.to_decimal()) / position.volume
                position.cost = PyDecimal(position.cost.to_decimal() + tax_cost)
                position_in_update = FundAccountPositionInUpdate(**position.dict())
                await update_fund_account_position_by_id(
                    db.client, position.id, position_in_update
                )
        await liquidation_fund_asset(db.client, portfolio)
    redis_key = f"{str_of_today()}_liquidate_dividend_tax"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(23, 59)))
