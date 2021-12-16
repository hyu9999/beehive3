import asyncio
from datetime import datetime, timedelta, time
from typing import List

import pandas as pd
from ability import FlowsStocksError
from ability.calculators.whole2 import WholeAbilityV2
from ability.models import FlowList, FundAssetList, StkAssetList
from aiohttp import ServerDisconnectedError
from numpy import isnan
from pymongo import ReplaceOne, UpdateOne
from stralib import FastTdate

from app.core.errors import CalculateAbilityError
from app.crud.fund_account import bulk_write_fund_account
from app.crud.portfolio import (
    bulk_write_portfolio,
    bulk_write_portfolio_analysis,
    get_portfolio_list,
)
from app.crud.time_series_data import (
    bulk_write_portfolio_assessment_time_series_data,
    get_fund_time_series_data,
    get_position_time_series_data,
)
from app.db.mongodb import db
from app.dec.scheduler import print_execute_time
from app.enums.portfolio import PortfolioCategory, 组合状态
from app.extentions import logger
from app.global_var import G
from app.models.base.portfolio import 个股统计信息, 交易统计信息, 用户资金账户信息, 组合阶段收益
from app.models.portfolio import PortfolioAnalysisInDB
from app.models.rwmodel import PyObjectId
from app.models.time_series_data import PortfolioAssessmentTimeSeriesDataInDB
from app.outer_sys.hq import get_security_info
from app.schema.portfolio import PortfolioInResponse
from app.service.check_status import CheckStatus
from app.service.datetime import get_early_morning, shift_month_datetime, str_of_today
from app.service.fund_account.fund_account import get_fund_account_flow
from app.service.time_series_data.converter import (
    field_converter,
    fund_time_series_data2ability,
    position_time_series_data2ability,
)
from app.utils.datetime import date2tdate, get_seconds


async def get_ability_flows(
    start_date: datetime,
    end_date: datetime,
    fund_account_list: List[用户资金账户信息],
    category: PortfolioCategory,
) -> FlowList:
    """获取资金账户ID列表内所有流水."""
    portfolio_flow_list = []
    for fund_account in fund_account_list:
        fund_account_flow_list = await get_fund_account_flow(
            db.client,
            fund_id=fund_account.fundid,
            start_date=start_date,
            end_date=end_date,
            category=category,
            currency=fund_account.currency,
            trade_only=False
        )
        portfolio_flow_list.extend(
            [field_converter(flow.dict()) for flow in fund_account_flow_list]
        )
    return FlowList.from_list(portfolio_flow_list)


async def get_ability_assets(
    start_date: datetime, end_date: datetime, fund_id_list: List[str]
) -> FundAssetList:
    """获取资金账户ID列表内所有资产时点数据."""
    portfolio_fund_time_series_list = []
    for fund_id in fund_id_list:
        fund_time_series_list = await get_fund_time_series_data(
            db.client,
            fund_id=fund_id,
            start_date=start_date.date(),
            end_date=end_date.date(),
        )
        portfolio_fund_time_series_list.extend(
            [fund_time_series_data2ability(fund) for fund in fund_time_series_list]
        )
    return FundAssetList.from_list(portfolio_fund_time_series_list)


async def get_ability_stocks(
    start_date: datetime, end_date: datetime, fund_id_list: List[str]
) -> StkAssetList:
    """获取资金账户ID列表内所有持仓时点数据."""
    portfolio_position_time_series_dict = {}
    for fund_id in fund_id_list:
        position_time_series_list = await get_position_time_series_data(
            db.client,
            fund_id=fund_id,
            start_date=start_date.date(),
            end_date=end_date.date(),
        )
        for position_time_series in position_time_series_list:
            # position_time_series为某一天的资金账户持仓
            if portfolio_position_time_series_dict.get(position_time_series.tdate):
                portfolio_position_time_series_dict[position_time_series.tdate].update(
                    position_time_series_data2ability(position_time_series)
                )
            else:
                portfolio_position_time_series_dict[
                    position_time_series.tdate
                ] = position_time_series_data2ability(position_time_series)
    return StkAssetList.from_list(portfolio_position_time_series_dict)


async def update_portfolio_stage_profit(
    ability_df: pd.DataFrame, portfolio_id: PyObjectId
) -> UpdateOne:
    """更新组合阶段收益数据."""
    stage_profit = 组合阶段收益(
        total=ability_df.iloc[-1]["累计收益率"],
        last_tdate=ability_df.iloc[-2]["收益率"],
        last_week=ability_df.iloc[-1]["近一周收益率"],
        last_month=ability_df.iloc[-1]["近一月收益率"],
        last_3_month=ability_df.iloc[-1]["近一季度收益率"],
        last_half_yar=ability_df.iloc[-1]["近半年收益率"],
        last_year=ability_df.iloc[-1]["近一年收益率"],
    )
    return UpdateOne({"_id": portfolio_id}, {"$set": stage_profit.dict()}, upsert=True)


async def create_portfolio_assessment_time_series_data(
    portfolio_id: PyObjectId,
    ability_df: pd.DataFrame,
) -> List[ReplaceOne]:
    """创建组合评估时点数据."""
    operations = []

    def round_val(v: float):
        return round(v, 5)

    for index, row in ability_df.iterrows():
        tdate = index.to_pydatetime()
        assessment = PortfolioAssessmentTimeSeriesDataInDB(
            portfolio=portfolio_id, tdate=tdate
        )
        assessment.account_yield = round_val(row["累计收益率"].values[0])
        assessment.accumulated_gain = row["累计收益"].values[0]
        assessment.max_drawdown = row["最大回撤"].values[0]
        assessment.sharpe_ratio = row["夏普比率"].values[0]
        assessment.annual_rate = round_val(row["年化收益率"].values[0])
        assessment.mktval_volatility = row["收益波动率"].values[0]
        assessment.turnover_rate = row["资金周转率"].values[0]
        gain_days = row["盈利天数"].values[0]
        trade_days = row["交易天数"].values[0]
        lost_days = trade_days - gain_days
        assessment.profit_loss_ratio = 1 if lost_days == 0 else gain_days / lost_days
        assessment.winning_rate = row["胜率"].values[0]
        assessment.abnormal_yield = round_val(row["超额收益率"].values[0])
        assessment.trade_cost = row["交易成本"].values[0]
        operations.append(
            ReplaceOne(
                {"portfolio": assessment.portfolio, "tdate": assessment.tdate},
                assessment.dict(exclude={"id"}),
                upsert=True,
            )
        )
    return operations


def get_tdate_by_stage(tdate: datetime, stage: str) -> datetime:
    """通过阶段字符串来获取具体的交易日."""
    stage_tdate_mapping = {
        "last_tdate": FastTdate.last_tdate(tdate),
        "last_week": tdate - timedelta(weeks=1),
        "last_month": shift_month_datetime(tdate, months=-1),
        "last_3_month": shift_month_datetime(tdate, months=-3),
        "last_half_year": shift_month_datetime(tdate, months=-6),
        "last_year": shift_month_datetime(tdate, months=-12),
    }
    return stage_tdate_mapping[stage]


def get_trade_stats(ability_df: pd.DataFrame) -> 交易统计信息:
    """获取交易统计信息."""

    def get_value_by_key(key):
        return float(ability_df.iloc[-1:][key].values[0])

    trade_stats = 交易统计信息()
    trade_stats.trade_frequency = get_value_by_key("交易次数")
    trade_stats.winning_rate = get_value_by_key("胜率")
    trade_stats.profit_loss_ratio = get_value_by_key("盈亏比")
    trade_stats.trade_cost = get_value_by_key("交易成本")
    return trade_stats


async def get_stock_stats(ability_df: pd.DataFrame) -> List[个股统计信息]:
    """获取个股统计信息."""

    def column_of(dataframe, key, item):
        return dataframe[key][item["symbol"]][item["exchange"]]

    ability_df = ability_df.loc[:, ["个股资金变动", "个股持仓变动", "个股收益率", "个股盈亏额"]]
    ability_df.rename(
        columns={"CNSESZ": "0", "CNSESH": "1", "": "2", "XSHG": "1", "XSHE": "0"},
        inplace=True,
    )
    stocks_df = ability_df.iloc[-1:]["个股收益率"].reset_index(drop=True).T.reset_index()
    stocks_df.rename(columns={0: "profit_rate"}, inplace=True)
    stocks_list = stocks_df.to_dict("records")
    stock_stats = []
    for stock in stocks_list:
        select_df = ability_df[column_of(ability_df, "个股资金变动", stock) < 0]
        trade_frequency, _ = ability_df[
            column_of(ability_df, "个股资金变动", stock) != 0
        ].shape
        sum_df = select_df.apply(sum, axis=0)
        cost = sum_df.loc["个股资金变动", stock["symbol"], stock["exchange"]]
        quantity = sum_df.loc["个股持仓变动", stock["symbol"], stock["exchange"]]
        if quantity and quantity != 0 and cost:
            stock["cost_price"] = -cost / quantity
        else:
            stock["cost_price"] = 0
        if isnan(stock["cost_price"]):
            stock["cost_price"] = 0
        stock["profit"] = column_of(ability_df.iloc[-1:], "个股盈亏额", stock).values[0]
        stock["trade_frequency"] = trade_frequency
        security = await get_security_info(
            symbol=stock["symbol"], exchange=stock["exchange"]
        )
        stock["symbol_name"] = security.symbol_name
        stock_stats.append(个股统计信息(**stock))
    return stock_stats


async def update_portfolio_analysis(
    portfolio: PortfolioInResponse, tdate: datetime
) -> UpdateOne:
    """更新组合阶段统计数据."""
    portfolio_analysis = PortfolioAnalysisInDB(portfolio=portfolio.id).dict()
    for stage in [
        "last_tdate",
        "last_week",
        "last_month",
        "last_3_month",
        "last_half_year",
        "last_year",
    ]:
        try:
            ability_df = await calculate_portfolio_ability(
                portfolio, get_tdate_by_stage(tdate, stage), tdate
            )
        except (
            AssertionError,
            FlowsStocksError,
            CalculateAbilityError,
            ServerDisconnectedError,
        ) as e:
            logger.warning(f"更新组合`{portfolio.id}`{stage}阶段统计数据失败({e}).")
        else:
            portfolio_analysis[stage] = {
                "trade_stats": get_trade_stats(ability_df),
                "stock_stats": await get_stock_stats(ability_df),
            }
        await asyncio.sleep(0.1)
    return UpdateOne(
        {"_id": portfolio.id},
        {"$set": PortfolioAnalysisInDB(**portfolio_analysis).dict(exclude={"id"})},
        upsert=True,
    )


async def calculate_portfolio_ability(
    portfolio: PortfolioInResponse,
    start_date: datetime,
    end_date: datetime,
):
    """计算组合战斗力数据."""
    fund_id_list = [fund_account.fundid for fund_account in portfolio.fund_account]
    ability_flows = await get_ability_flows(
        portfolio.import_date, end_date, portfolio.fund_account, portfolio.category
    )
    ability_assets = await get_ability_assets(start_date, end_date, fund_id_list)
    ability_stocks = await get_ability_stocks(start_date, end_date, fund_id_list)
    if ability_assets.df.empty or ability_stocks.df.empty:
        raise CalculateAbilityError(
            f"未查询到组合`{portfolio.id}`{start_date}~{end_date}的时点数据."
        )
    abi = WholeAbilityV2(
        str(portfolio.id),
        start_date,
        end_date,
        ability_assets,
        ability_flows,
        ability_stocks,
    )
    ability, _ = abi.calc_ability()
    return ability


async def calculate_ability(portfolio_list: List[PortfolioInResponse]):
    """计算战斗力任务."""
    if not FastTdate.is_tdate():
        return None
    # 等待时点数据同步完成
    while not await CheckStatus.check_time_series_status():
        await asyncio.sleep(10)
    tdate = get_early_morning()
    portfolio_operations = []
    portfolio_assessment_time_series_operations = []
    portfolio_analysis_operations = []
    fund_account_operations = []
    for portfolio in portfolio_list:
        start_date = date2tdate(portfolio.import_date)
        try:
            ability = await calculate_portfolio_ability(portfolio, start_date, tdate)
        except (
            CalculateAbilityError,
            FlowsStocksError,
            AssertionError,
            ServerDisconnectedError,
        ) as e:
            logger.warning(f"计算组合`{portfolio.id}`的战斗力错误, 已跳过({e}).")
            continue
        # 更新组合阶段收益率
        portfolio_operations.append(
            await update_portfolio_stage_profit(ability, portfolio.id)
        )
        # 更新组合分析数据
        portfolio_analysis_operations.append(
            await update_portfolio_analysis(portfolio, tdate)
        )
        # 创建组合评估时点数据
        portfolio_assessment_time_series_operations.extend(
            await create_portfolio_assessment_time_series_data(portfolio.id, ability)
        )
        # 更新资金账户时点数据同步日期为今日
        for fund_account in portfolio.fund_account:
            fund_account_operations.append(
                UpdateOne(
                    {"_id": PyObjectId(fund_account.fundid)},
                    {"$set": {"ts_data_sync_date": tdate}},
                )
            )
    if portfolio_operations:
        await bulk_write_portfolio(db.client, portfolio_operations)
    if portfolio_analysis_operations:
        await bulk_write_portfolio_analysis(db.client, portfolio_analysis_operations)
    if portfolio_assessment_time_series_operations:
        await bulk_write_portfolio_assessment_time_series_data(
            db.client, portfolio_assessment_time_series_operations
        )
    if fund_account_operations:
        await bulk_write_fund_account(db.client, fund_account_operations)


@print_execute_time
async def calculate_manual_import_portfolio_ability_task():
    """计算手动导入组合战斗力数据."""
    portfolio_list = await get_portfolio_list(
        db.client, {"status": 组合状态.running, "category": PortfolioCategory.ManualImport}
    )
    await calculate_ability(portfolio_list)
    redis_key = f"{str_of_today()}_ability"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(23, 59)))


@print_execute_time
async def calculate_simulated_trading_portfolio_ability_task():
    """计算模拟交易组合战斗力数据."""
    portfolio_list = await get_portfolio_list(
        db.client,
        {"status": 组合状态.running, "category": PortfolioCategory.SimulatedTrading},
    )
    await calculate_ability(portfolio_list)
    redis_key = f"{str_of_today()}_ability"
    await G.scheduler_redis.set(redis_key, "1", get_seconds(time(22, 0)))
