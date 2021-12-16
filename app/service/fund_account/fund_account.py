from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Union

import numpy as np
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app.core.errors import EntityDoesNotExist, RegisterExternalSystemFailed
from app.crud.fund_account import (
    create_fund_account_position,
    delete_fund_account_position_by_id,
    get_fund_account_by_id,
    get_fund_account_flow_from_db,
    get_fund_account_position_from_db,
    update_fund_account_by_id,
    update_fund_account_position_by_id,
)
from app.crud.portfolio import (
    get_portfolio_by_fund_id,
    get_portfolio_by_id,
    update_portfolio_import_date_by_id,
)
from app.enums.fund_account import CurrencyType, Exchange, FlowTType
from app.enums.portfolio import PortfolioCategory
from app.extentions import logger
from app.global_var import G
from app.models.base.portfolio import 用户资金账户信息
from app.models.fund_account import (
    FundAccountFlowInDB,
    FundAccountInDB,
    FundAccountPositionInDB,
)
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyDecimal, PyObjectId
from app.outer_sys.hq import get_security_price
from app.schema.fund_account import (
    FundAccountFlowInCreate,
    FundAccountInUpdate,
    FundAccountPositionInUpdate,
    FundAccountPositionList,
)
from app.service.check_status import CheckStatus
from app.service.time_series_data.converter import pt_flow2beehive_flow
from app.utils.datetime import date2datetime, get_utc_now
from app.utils.exchange import convert_exchange


def calculate_flow_fee(
    fund_account: FundAccountInDB, flow: Union[FundAccountFlowInCreate]
) -> FundAccountFlowInDB:
    """计算流水费用."""
    # 发生金额
    amount = abs(flow.cost.to_decimal()) * abs(flow.stkeffect)
    if flow.ttype == FlowTType.BUY:
        # 证券金额
        security_amount = amount / (1 + fund_account.commission.to_decimal())
        commission = security_amount * fund_account.commission.to_decimal()
        tax = 0
        direction = -1
    else:
        # 证券金额
        security_amount = amount / (
            1
            + fund_account.commission.to_decimal()
            + fund_account.tax_rate.to_decimal()
        )
        commission = security_amount * fund_account.commission.to_decimal()
        tax = security_amount * fund_account.tax_rate.to_decimal()
        direction = 1
    commission, tax = round(commission, 4), round(tax, 4)
    # 若为买单 stkeffect为正 fundeffect为负
    # 若为卖单 stkeffect为负 fundeffect为正
    flow.stkeffect = abs(flow.stkeffect) * direction * -1
    flow.ts = get_utc_now().timestamp()
    return FundAccountFlowInDB(
        **flow.dict(),
        total_fee=commission + tax,
        fundeffect=amount * direction,
        commission=commission,
        tax=tax,
        tprice=round(security_amount / abs(flow.stkeffect), 4),
    )


async def update_fund_account_by_flow(
    conn: AsyncIOMotorClient,
    fund_account: FundAccountInDB,
    flow: FundAccountFlowInDB,
    ts_data_sync_date: Optional[datetime] = None,
) -> None:
    """根据资金账户流水更新资金账户资产."""

    position_list = await get_fund_account_position_from_db(
        conn, fund_id=str(fund_account.id)
    )
    cash = fund_account.cash.to_decimal() + flow.fundeffect.to_decimal()
    securities = Decimal(0)
    for position in position_list:
        security = await get_security_price(
            symbol=position.symbol,
            exchange=convert_exchange(position.exchange, to="beehive"),
        )
        securities += security.current * position.volume
    if ts_data_sync_date is None:
        if FastTdate.last_tdate(flow.tdate) < fund_account.ts_data_sync_date:
            ts_data_sync_date = FastTdate.last_tdate(flow.tdate)
        else:
            ts_data_sync_date = fund_account.ts_data_sync_date
    fund_account_in_update = FundAccountInUpdate(
        cash=cash,
        securities=securities,
        ts_data_sync_date=ts_data_sync_date,
        assets=cash + securities,
    )
    await update_fund_account_by_id(
        conn, PyObjectId(flow.fund_id), fund_account_in_update
    )


async def update_position_by_flow(
    conn: AsyncIOMotorClient,
    flow: FundAccountFlowInDB,
) -> None:
    """根据资金账户流水更新持仓信息."""
    position = await get_fund_account_position_from_db(
        conn, fund_id=flow.fund_id, symbol=flow.symbol, exchange=flow.exchange
    )
    if position:
        position = position[0]
        volume = position.volume + flow.stkeffect
        if volume == 0:
            await delete_fund_account_position_by_id(conn, position.id)
        else:
            # 持仓成本 = (原持仓总成本 + 流水持仓总成本) / 持仓数量
            # 流水为卖单时，流水持仓总成本为负
            cost = (
                position.cost.to_decimal() * position.volume
                + flow.cost.to_decimal() * flow.stkeffect
            ) / volume
            position_in_update = FundAccountPositionInUpdate(
                volume=volume,
                cost=round(cost, 4),
            )
            await update_fund_account_position_by_id(
                conn, position.id, position_in_update
            )
    else:
        position = FundAccountPositionInDB(
            fund_id=flow.fund_id,
            symbol=flow.symbol,
            exchange=flow.exchange,
            volume=abs(flow.stkeffect),
            cost=flow.cost,
        )
        await create_fund_account_position(conn, position)


async def get_portfolio_position(
    conn: AsyncIOMotorClient,
    portfolio_id: PyObjectId,
) -> List[FundAccountPositionList]:
    """获取组合持仓."""
    portfolio = await get_portfolio_by_id(conn, portfolio_id)
    fund_account_position_list = []
    for fund_account in portfolio.fund_account:
        fund_account_position = FundAccountPositionList(
            fund_id=fund_account.fundid,
            currency=fund_account.currency,
        )
        fund_account_position.position_list = await get_fund_account_position(
            conn, fund_account.fundid, portfolio.category
        )
        fund_account_position_list.append(fund_account_position)
    return fund_account_position_list


async def get_fund_account_position(
    conn: AsyncIOMotorClient, fund_id: str, category: PortfolioCategory
) -> Optional[List[FundAccountPositionInDB]]:
    """获取资金账户持仓列表."""
    # 类型为手动导入组合的持仓
    if category == PortfolioCategory.ManualImport:
        fund_account_position_list = await get_fund_account_position_from_db(
            conn, fund_id=fund_id
        )
    # 类型为模拟交易组合的持仓
    else:
        tir = await G.trade_system.get_fund_stock(fund_id=fund_id, convert_out=False)
        if tir.flag and tir.data:
            fund_account_position_list = []
            for position in tir.data:
                position["exchange"] = (
                    Exchange.CNSESH if position["exchange"] == "SH" else Exchange.CNSESZ
                )
                fund_account_position_list.append(
                    FundAccountPositionInDB(**position, fund_id=fund_id)
                )
        else:
            fund_account_position_list = []
    return fund_account_position_list


async def get_portfolio_fund_list(
    conn: AsyncIOMotorClient,
    portfolio_id: PyObjectId,
) -> List[FundAccountInDB]:
    """获取组合资金账户资产列表."""
    portfolio = await get_portfolio_by_id(conn, portfolio_id)
    fund_account_fund_list = []
    # 类型为手动导入组合的资产
    if portfolio.category == PortfolioCategory.ManualImport:
        for fund_account_item in portfolio.fund_account:
            try:
                fund_account = await get_fund_account_by_id(
                    conn, PyObjectId(fund_account_item.fundid)
                )
            except EntityDoesNotExist:
                logger.warning(f"获取资金账户`{fund_account_item.fundid}`失败, 该资金账户不存在.")
                continue
            else:
                fund_account_fund_list.append(fund_account)
    # 类型为模拟交易组合的资产
    else:
        for fund_account in portfolio.fund_account:
            tir = await G.trade_system.get_fund_asset(
                fund_id=fund_account.fundid, convert_out=False
            )
            if not tir.data:
                logger.warning(f"获取资金账户`{fund_account.fundid}`失败, 该资金账户不存在.")
                continue
            else:
                fund_account_fund_list.append(
                    FundAccountInDB(
                        **tir.data,
                        id=fund_account.fundid,
                        currency=fund_account.currency,
                        ts_data_sync_date=FastTdate.last_tdate(date2datetime()),
                    )
                )
    return fund_account_fund_list


async def get_fund_account_flow(
    conn: AsyncIOMotorClient,
    fund_id: str,
    category: PortfolioCategory,
    currency: CurrencyType,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    ttype: Optional[List[FlowTType]] = None,
    symbol: Optional[str] = None,
    trade_only: bool = True,
) -> List[FundAccountFlowInDB]:
    """获取资金账户流水."""
    # 类型为手动导入组合的流水
    if category == PortfolioCategory.ManualImport:
        flow_list = await get_fund_account_flow_from_db(
            conn,
            fund_id=fund_id,
            start_date=start_date,
            end_date=end_date,
            ttype=ttype,
            symbol=symbol,
        )
    # 类型为模拟交易组合的流水
    else:
        if ttype is not None and [
            item for item in ttype if item in [FlowTType.DEPOSIT, FlowTType.WITHDRAW]
        ]:
            flow_list = []
        else:
            if start_date is not None:
                start_date = start_date.strftime("%Y%m%d")
            if end_date is not None:
                end_date = end_date.strftime("%Y%m%d")
            flow_raw = await G.trade_system.get_statement(
                fund_id, start_date=start_date, stop_date=end_date, convert_out=False
            )
            if isinstance(flow_raw.data, list):
                flow_list = [
                    pt_flow2beehive_flow(flow, currency) for flow in flow_raw.data
                ]
            else:
                flow_list = []
            if symbol is not None:
                flow_list = [flow for flow in flow_list if flow.symbol == symbol]
            if trade_only:
                flow_list = [
                    flow
                    for flow in flow_list
                    if flow.ttype in [FlowTType.BUY, FlowTType.SELL]
                ]
    return flow_list


async def get_fund_asset(
    conn: AsyncIOMotorClient,
    fund_id: str,
    category: PortfolioCategory,
    currency: CurrencyType,
) -> FundAccountInDB:
    """获取资金账户"""
    # 类型为手动导入组合的资产
    if category == PortfolioCategory.ManualImport:
        return await get_fund_account_by_id(conn, PyObjectId(fund_id))
    # 类型为模拟交易组合的资产
    else:
        tir = await G.trade_system.get_fund_asset(fund_id=fund_id, convert_out=False)
        if tir.flag:
            if await CheckStatus.check_ability_status():
                ts_data_sync_date = (
                    date2datetime()
                    if FastTdate.is_tdate(date2datetime())
                    else FastTdate.last_tdate(date2datetime())
                )
            else:
                ts_data_sync_date = FastTdate.last_tdate(date2datetime())
            return FundAccountInDB(
                **tir.data,
                id=fund_id,
                currency=currency,
                ts_data_sync_date=ts_data_sync_date,
            )
        raise EntityDoesNotExist


async def calculate_fund_asset(
    conn: AsyncIOMotorClient, fund_account: FundAccountInDB
) -> FundAccountInDB:
    """计算最新资金账户数据(同步用户持仓证券市值和总资产)."""
    position_list = await get_fund_account_position_from_db(
        conn, fund_id=str(fund_account.id)
    )
    securities = Decimal(0)
    for position in position_list:
        security = await get_security_price(
            symbol=position.symbol,
            exchange=convert_exchange(position.exchange, to="beehive"),
        )
        securities += security.current * position.volume
    fund_account.securities = PyDecimal(securities)
    fund_account.assets = PyDecimal(securities + fund_account.cash.to_decimal())
    return fund_account


async def set_portfolio_import_date(
    conn: AsyncIOMotorClient, fund_account: FundAccountInDB
) -> datetime:
    """处理组合的最早导入持仓时间."""
    portfolio = await get_portfolio_by_fund_id(conn, str(fund_account.id))
    flow_list = await get_fund_account_flow_from_db(conn, fund_id=str(fund_account.id))
    import_date = min([flow.tdate for flow in flow_list] + [portfolio.create_date])
    import_date = FastTdate.last_tdate(import_date)
    await update_portfolio_import_date_by_id(
        conn, portfolio.id, import_date=import_date
    )
    return import_date


async def generate_simulation_account(
    portfolio_id: str, total_input: float
) -> 用户资金账户信息:
    """生成模拟账户."""
    tir = await G.trade_system.bind_fund_account(portfolio_id, total_input)
    if not tir.flag:
        raise RegisterExternalSystemFailed()
    fund_account = 用户资金账户信息(
        userid=portfolio_id, fundid=str(tir.data["fund_id"]), create_date=get_utc_now()
    )
    return fund_account


async def get_net_deposit_flow(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    start_date: date,
    end_date: date,
    include_capital: bool = True,
    include_today: bool = False,
) -> pd.Series:
    """获取组合净入金."""
    fund_account = portfolio.fund_account[0]
    flow_list = await get_fund_account_flow(
        conn,
        fund_account.fundid,
        portfolio.category,
        fund_account.currency,
        start_date=start_date,
        end_date=end_date,
        ttype=[FlowTType.DEPOSIT, FlowTType.WITHDRAW],
    )
    if include_capital:
        flow_raw = {portfolio.import_date.date(): Decimal(portfolio.initial_funding)}
    else:
        flow_raw = {}
    for flow in flow_list:
        if not include_today and flow.created_at.date() == datetime.today().date():
            continue
        tdate = flow.tdate.date()
        if tdate in flow_raw.keys():
            flow_raw[tdate] += flow.fundeffect.to_decimal()
        else:
            flow_raw[tdate] = flow.fundeffect.to_decimal()
    return pd.Series(flow_raw, dtype=np.float64, name="当日净入金_中间值")


def calculation_simple(
    net_deposit_day: pd.Series, stock_asset_value: pd.Series
) -> float:
    """简单收益率."""

    profit = stock_asset_value[-1] - stock_asset_value[0] - net_deposit_day.sum()
    if profit == 0:
        rv = 0
    else:
        rv = profit / stock_asset_value[0]
    return rv


def calculation_simple_ability(
    net_deposit_day: pd.Series, stock_asset_value: pd.Series
) -> float:
    """简单收益率(战斗力版本)."""
    data = pd.DataFrame([stock_asset_value, net_deposit_day]).T.fillna(0)
    data["股票资产_1"] = data["股票资产"].shift(1).fillna(method="bfill")
    data = data.eval("收益 = 股票资产 - 股票资产_1 - 当日净入金_中间值").fillna(0)
    data["当日净入金_中间值"] = data["当日净入金_中间值"].apply(lambda x: max(x, 0))
    data = data.eval("收益率 = 收益 / (股票资产_1 + 当日净入金_中间值)").fillna(0)
    return ((data["收益率"] + 1).cumprod() - 1)[-1]


async def liquidation_fund_asset(
    conn: AsyncIOMotorClient, portfolio: Portfolio
) -> None:
    """清算手动导入资金账户资产数据."""
    old_fund_account = await get_fund_account_by_id(
        conn, PyObjectId(portfolio.fund_account[0].fundid)
    )
    new_fund_account = await calculate_fund_asset(conn, old_fund_account)
    await update_fund_account_by_id(
        conn, new_fund_account.id, FundAccountInUpdate(**new_fund_account.dict())
    )
