import asyncio
from datetime import datetime, time
from typing import List, Tuple

from ability.operators import ReverseFlowsOperator
from aiohttp import ServerDisconnectedError
from pymongo import DeleteOne, ReplaceOne, UpdateOne
from stralib import FastTdate
from stralib.utils import listdict2dict

from app.crud.fund_account import bulk_write_fund_account
from app.crud.portfolio import get_portfolio_list
from app.crud.time_series_data import (
    bulk_write_fund_time_series_data,
    bulk_write_position_time_series_data,
    get_fund_time_series_data,
    get_position_time_series_data,
)
from app.db.mongodb import db
from app.dec.scheduler import print_execute_time
from app.enums.fund_account import CurrencyType
from app.enums.portfolio import PortfolioCategory, 组合状态
from app.extentions import logger
from app.global_var import G
from app.models.fund_account import FundAccountInDB
from app.models.time_series_data import (
    FundTimeSeriesDataInDB,
    PositionTimeSeriesDataInDB,
)
from app.schema.fund_account import FundAccountInUpdate
from app.schema.portfolio import PortfolioInResponse
from app.service.check_status import CheckStatus
from app.service.datetime import get_early_morning, str_of_today
from app.service.fund_account.fund_account import (
    calculate_fund_asset,
    get_fund_account_flow,
    get_fund_account_position,
    get_portfolio_fund_list,
)
from app.service.time_series_data.converter import (
    ability2fund_time_series_data,
    ability2position_time_series_data,
    field_converter,
    fund2time_series,
    fund_time_series_data2ability,
    position2time_series,
    position_time_series_data2ability,
)
from app.utils.datetime import date2datetime, date2tdate, get_seconds


async def save_today_time_series_data(
    fund_account: FundAccountInDB, tdate: datetime, category: PortfolioCategory
) -> Tuple[ReplaceOne, ReplaceOne]:
    """保存当前交易日时点数据.

    Parameters
    ----------
    fund_account: 资金账户
    tdate: 当前交易日
    category: 组合类别

    Returns
    ----------
    持仓时点数据, 资产时点数据
    """
    fund_id = str(fund_account.id)

    # 持仓时点数据
    position_time_series_data = await position2time_series(
        await get_fund_account_position(db.client, fund_id=fund_id, category=category),
        fund_id,
        tdate,
    )
    # 资产时点数据
    fund_time_series_data = fund2time_series(fund_account, tdate)
    return ReplaceOne(
        {"tdate": tdate, "fund_id": fund_id},
        position_time_series_data.dict(exclude={"id"}),
        upsert=True,
    ), ReplaceOne(
        {"tdate": tdate, "fund_id": fund_id},
        fund_time_series_data.dict(exclude={"id"}),
        upsert=True,
    )


async def generate_history_time_series_data(
    fund_account: FundAccountInDB,
    start: datetime,
    end: datetime,
    category: PortfolioCategory,
    currency: CurrencyType,
) -> Tuple[List[PositionTimeSeriesDataInDB], List[FundTimeSeriesDataInDB]]:
    fund_id = str(fund_account.id)
    # 由于这里的计算逻辑为向以前交易日推算数据，所以传参时start=end, end=start
    end = FastTdate.transfer2closed(end)
    # 时点数据同步日到今天的所有流水
    flow_list = await get_fund_account_flow(
        db.client,
        fund_id=fund_id,
        start_date=start.date(),
        end_date=end.date(),
        category=category,
        currency=currency,
        trade_only=False,
    )
    rfo = ReverseFlowsOperator(
        fundId=fund_id,
        start=end,
        end=start,
        symbol_list=[
            flow.symbol for flow in flow_list if flow.symbol and flow.symbol != "SYMBOL"
        ],
    )
    # 当前用户持仓
    fund_account_position = await get_fund_account_position(
        db.client, fund_id=fund_id, category=category
    )
    # 转换为时点数据格式
    position_time_series_data = await position2time_series(
        fund_account_position, fund_id, end
    )
    init_stocks = {end: position_time_series_data2ability(position_time_series_data)}
    init_assets = {
        end: fund_time_series_data2ability(fund2time_series(fund_account, end))
    }
    fund_time_series_list, _, position_time_series_list = rfo.generate(
        flows=listdict2dict(
            [field_converter(flow.dict()) for flow in flow_list], key="tdate"
        ),
        init_assets=init_assets,
        init_stocks=init_stocks,
    )
    return (
        ability2position_time_series_data(fund_id, position_time_series_list),
        ability2fund_time_series_data(fund_time_series_list),
    )


async def save_history_time_series_data(
    fund_account: FundAccountInDB,
    start: datetime,
    end: datetime,
    category: PortfolioCategory,
    currency: CurrencyType,
) -> Tuple[List[ReplaceOne], List[ReplaceOne]]:
    """保存历史交易日时点数据.

    Parameters
    ----------
    fund_account: 资金账户
    start: 开始时间
    end: 结束时间
    category: 组合类别
    currency: 币种
    """
    (
        position_time_series_list,
        fund_time_series_list,
    ) = await generate_history_time_series_data(
        fund_account, start, end, category, currency
    )
    return [
        ReplaceOne(
            {"tdate": fund.tdate, "fund_id": fund.fund_id},
            fund.dict(exclude={"id"}),
            upsert=True,
        )
        for fund in position_time_series_list
    ], [
        ReplaceOne(
            {"tdate": fund.tdate, "fund_id": fund.fund_id},
            fund.dict(exclude={"id"}),
            upsert=True,
        )
        for fund in fund_time_series_list
    ]


async def save_time_series_data(portfolio_list: List[PortfolioInResponse]):
    """保存资金账户时点数据."""
    if not FastTdate.is_tdate():
        return None
    tdate = date2datetime()
    position_time_series_operations = []
    fund_time_series_operations = []
    for portfolio in portfolio_list:
        fund_account_list = await get_portfolio_fund_list(db.client, portfolio.id)
        if not fund_account_list:
            logger.warning(f"组合`{portfolio.id}`无可用资金账户, 已跳过处理.")
        for fund_account in fund_account_list:
            # 若时点数据同步时间为上一个交易日, 写入今日资金账户数据到时点数据
            if fund_account.ts_data_sync_date == FastTdate.last_tdate(datetime.today()):
                try:
                    (
                        position_time_series_opt,
                        fund_time_series_opt,
                    ) = await save_today_time_series_data(
                        fund_account, tdate, portfolio.category
                    )
                except (IndexError, AssertionError) as e:
                    logger.warning(f"处理组合`{portfolio.id}`时点数据失败, 已跳过处理({e}).")
                    continue
                position_time_series_operations.append(position_time_series_opt)
                fund_time_series_operations.append(fund_time_series_opt)
            # 若时点数据同步时间不为上一个交易日, 重写时点数据同步日到今日的所有时点数据
            else:
                # 开始时间为流水同步日期
                start = fund_account.ts_data_sync_date
                # 结束时间为当前交易日
                end = tdate
                # 删除失效的时点数据
                for position_time_series_data in await get_position_time_series_data(
                    db.client,
                    fund_id=str(fund_account.id),
                    start_date=FastTdate.next_tdate(start).date(),
                    end_date=end.date(),
                ):
                    position_time_series_operations.append(
                        DeleteOne({"_id": position_time_series_data.id})
                    )
                for fund_time_series_data in await get_fund_time_series_data(
                    db.client,
                    fund_id=str(fund_account.id),
                    start_date=FastTdate.next_tdate(start).date(),
                    end_date=end.date(),
                ):
                    fund_time_series_operations.append(
                        DeleteOne({"_id": fund_time_series_data.id})
                    )
                try:
                    # 补全时点数据
                    (
                        position_time_series_opt,
                        fund_time_series_opt,
                    ) = await save_history_time_series_data(
                        fund_account,
                        start,
                        end,
                        portfolio.category,
                        fund_account.currency,
                    )
                except (IndexError, ServerDisconnectedError) as e:
                    logger.warning(f"处理组合`{portfolio.id}`时点数据失败, 已跳过处理({e}).")
                    continue
                position_time_series_operations.extend(position_time_series_opt)
                fund_time_series_operations.extend(fund_time_series_opt)
            await asyncio.sleep(0.1)
    if position_time_series_operations:
        await bulk_write_position_time_series_data(
            db.client, position_time_series_operations
        )
    if fund_time_series_operations:
        await bulk_write_fund_time_series_data(db.client, fund_time_series_operations)


@print_execute_time
async def save_manual_import_portfolio_time_series_data_task():
    """保存手动导入组合时点数据."""
    portfolio_list = await get_portfolio_list(
        db.client, {"status": 组合状态.running, "category": PortfolioCategory.ManualImport}
    )
    await save_time_series_data(portfolio_list)
    redis_key = f"{str_of_today()}_time_series_data"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(22, 15)))


@print_execute_time
async def save_manual_import_portfolio_time_series_data_task2():
    while not await CheckStatus.check_liquidate_dividend_tax_status():
        await asyncio.sleep(10)
    portfolio_list = await get_portfolio_list(
        db.client, {"status": 组合状态.running, "category": PortfolioCategory.ManualImport}
    )
    await save_time_series_data(portfolio_list)
    redis_key = f"{str_of_today()}_time_series_data"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(23, 59)))


@print_execute_time
async def save_simulated_trading_portfolio_time_series_data_task():
    """保存模拟交易组合时点数据."""
    portfolio_list = await get_portfolio_list(
        db.client,
        {"status": 组合状态.running, "category": PortfolioCategory.SimulatedTrading},
    )
    await save_time_series_data(portfolio_list)
    redis_key = f"{str_of_today()}_time_series_data"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(22, 0)))


@print_execute_time
async def liquidation_fund_asset_task():
    """清算手动导入资金账户资产数据."""
    portfolio_list = await get_portfolio_list(
        db.client, {"status": 组合状态.running, "category": PortfolioCategory.ManualImport}
    )
    operations = []
    for portfolio in portfolio_list:
        fund_account_list = await get_portfolio_fund_list(db.client, portfolio.id)
        if not fund_account_list:
            logger.warning(f"组合`{portfolio.id}`无可用资金账户, 已跳过处理.")
        for fund_account in fund_account_list:
            fund_asset = await calculate_fund_asset(db.client, fund_account)
            operations.append(
                UpdateOne(
                    {"_id": fund_account.id},
                    {"$set": FundAccountInUpdate(**fund_asset.dict()).dict()},
                )
            )
    if operations:
        await bulk_write_fund_account(db.client, operations)


@print_execute_time
async def sync_time_series_data_task():
    end = date2tdate(get_early_morning())
    portfolio_list = await get_portfolio_list(db.client, {"status": 组合状态.running})
    position_time_series_operations = []
    fund_time_series_operations = []

    for index, portfolio in enumerate(portfolio_list, start=1):
        fund_account_list = await get_portfolio_fund_list(db.client, portfolio.id)
        logger.info(f"[{index}/{len(portfolio_list)}]正在处理组合`{portfolio.id}`.")
        if not fund_account_list:
            logger.info(f"组合`{portfolio.id}`无可用资金账户, 已跳过处理.")
            continue
        # 开始时间设置为组合的最早持仓导入时间
        start = portfolio.import_date
        if start < datetime.fromisoformat("2021-01-01"):
            logger.info(f"组合`{portfolio.id}`导入时间早于2021-01-01, 已跳过处理.")
            continue
        for fund_account in fund_account_list:
            # 删除失效的时点数据
            for position_time_series_data in await get_position_time_series_data(
                db.client,
                fund_id=str(fund_account.id),
                start_date=start.date(),
                end_date=end.date(),
            ):
                position_time_series_operations.append(
                    DeleteOne({"_id": position_time_series_data.id})
                )
            for fund_time_series_data in await get_fund_time_series_data(
                db.client,
                fund_id=str(fund_account.id),
                start_date=start.date(),
                end_date=end.date(),
            ):
                fund_time_series_operations.append(
                    DeleteOne({"_id": fund_time_series_data.id})
                )
            logger.info(f"正在补全资金账户`{fund_account.id}`的时点数据.")
            # 补全时点数据
            try:
                (
                    position_time_series_opt,
                    fund_time_series_opt,
                ) = await save_history_time_series_data(
                    fund_account, start, end, portfolio.category, fund_account.currency
                )
            except (IndexError, ServerDisconnectedError, AssertionError) as e:
                logger.warning(f"处理组合`{portfolio.id}`时点数据失败, 已跳过处理({e}).")
                continue
            position_time_series_operations.extend(position_time_series_opt)
            fund_time_series_operations.extend(fund_time_series_opt)
            await asyncio.sleep(0.1)
    if position_time_series_operations:
        await bulk_write_position_time_series_data(
            db.client, position_time_series_operations
        )
    if fund_time_series_operations:
        await bulk_write_fund_time_series_data(db.client, fund_time_series_operations)
    redis_key = f"{end.strftime('%Y%m%d')}_time_series_data"
    await G.scheduler_redis.set(redis_key, "1", 60 * 60 * 8)
