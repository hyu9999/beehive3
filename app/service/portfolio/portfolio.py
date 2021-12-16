from calendar import monthrange
from datetime import date, datetime, timedelta
from math import ceil
from typing import Dict, List, Optional, Union

from ability.calculators.ratio_calculators import calculation_mwr, calculation_twr
from fastapi import HTTPException
from hq2redis import HQSourceError, SecurityNotFoundError
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from stralib import FastTdate, get_strategy_signal
from stralib.fb.date_time import shift_trade_day
from stralib.flow_operator.tdate import NeedUpdateError

from app import settings
from app.core.errors import EntityDoesNotExist, PortfolioTooMany
from app.crud.base import get_portfolio_collection
from app.crud.discuzq import create_thread
from app.crud.equipment import 查询某个装备的详情
from app.crud.fund_account import create_fund_account, update_fund_account_by_id
from app.crud.portfolio import create_portfolio, get_portfolio_by_id
from app.crud.robot import 查询某机器人信息
from app.crud.time_series_data import get_portfolio_assessment_time_series_data
from app.enums.common import DateType
from app.enums.portfolio import PortfolioCategory, ReturnYieldCalculationMethod, 组合状态
from app.extentions import logger
from app.models.base.portfolio import 用户资金账户信息
from app.models.fund_account import FundAccountInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.schema.fund_account import FundAccountInUpdate
from app.schema.portfolio import (
    PortfolioBasicRunDataInResponse,
    PortfolioInCreate,
    PortfolioInResponse,
)
from app.schema.user import User
from app.service.datetime import get_early_morning, str_of_today
from app.service.fund_account.converter import db_asset2frontend, db_position2frontend
from app.service.fund_account.fund_account import (
    calculate_fund_asset,
    calculation_simple_ability,
    generate_simulation_account,
    get_fund_account_position,
    get_fund_asset,
    get_net_deposit_flow,
    liquidation_fund_asset,
)
from app.service.time_series_data.time_series_data import get_assets_time_series_data
from app.utils.datetime import date2datetime, date2tdate


async def inspect_portfolio_number_limit(conn: AsyncIOMotorClient, user: User) -> None:
    """检查用户组合数量是否超出限制"""
    if not user.roles[0] == "超级用户":
        db_query = {
            "username": user.username,
            "status": 组合状态.running.value,
            "activity": {"$not": {"$exists": True, "$ne": None}},
        }
        count = await get_portfolio_collection(conn).count_documents(db_query)
        if count >= settings.num_limit[user.roles[0]]["portfolio"]:
            raise PortfolioTooMany(
                message=f"创建组合数达到上限，最多只能创建{settings.num_limit[user.roles[0]]['portfolio']}个"
            )


async def get_portfolio_profit_rate(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    start_date: date,
    end_date: date,
    calculation_method: ReturnYieldCalculationMethod,
) -> float:
    """根据日期获取组合收益率."""
    assets_list = await get_assets_time_series_data(
        conn, portfolio, start_date, end_date
    )
    if assets_list.empty:
        return 0
    if calculation_method == ReturnYieldCalculationMethod.SWR:
        if start_date < end_date:
            start_date = FastTdate.next_tdate(start_date)
        net_deposit_list = await get_net_deposit_flow(
            conn, portfolio, start_date, end_date, include_capital=False
        )
        rv = calculation_simple_ability(net_deposit_list, assets_list)
    elif calculation_method == ReturnYieldCalculationMethod.TWR:
        rv = calculation_twr(assets_list)[-1]
    elif calculation_method == ReturnYieldCalculationMethod.MWR:
        net_deposit_list = await get_net_deposit_flow(
            conn, portfolio, start_date, end_date
        )
        rv = calculation_mwr(net_deposit_list, assets_list)[-1]
    else:
        raise ValueError(f"还未支持收益率计算方式{calculation_method.value}.")
    return rv


def get_date_by_type(date_type: DateType, end_date=None):
    """根据date_type获取日期"""
    end_date = end_date or get_early_morning()
    if date_type == DateType.WEEK:
        start_date = end_date - timedelta(weeks=1)
    elif date_type == DateType.MONTH:
        _, month_days = monthrange(end_date.year, end_date.month)
        start_date = end_date - timedelta(days=month_days)
    elif date_type == DateType.DAY:
        start_date = end_date - timedelta(days=1)
    else:
        start_date = end_date
    if not FastTdate.is_tdate(start_date):
        start_date = FastTdate.last_tdate(start_date)
    return start_date


async def get_portfolio_yield_trend(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    start_date: datetime,
    end_date: datetime,
) -> List[Dict[str, Union[float, str]]]:
    """获取组合收益率趋势."""
    current_date = start_date
    data_list = []
    while True:
        loop_date = FastTdate.next_tdate(current_date)
        if current_date > end_date:
            break
        assessment = await get_portfolio_assessment_time_series_data(
            conn, portfolio=portfolio.id, tdate=current_date.date()
        )
        if assessment:
            tmp_dict = {
                "timestamp": current_date.strftime("%Y-%m-%d"),
                "profit_rate": assessment[0].account_yield,
            }
            data_list.append(tmp_dict)
        current_date = loop_date
    return data_list


async def get_yield_trend(
    conn: AsyncIOMotorClient,
    portfolio_id: PyObjectId,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> Dict[str, Union[PortfolioInResponse, List[Dict[str, Union[float, str]]]]]:
    """收益率趋势"""
    portfolio = await get_portfolio_by_id(conn, id=portfolio_id)
    if not portfolio:
        raise EntityDoesNotExist
    start_date = start_date or portfolio.import_date
    end_date = end_date or get_early_morning()
    if portfolio.category == PortfolioCategory.ManualImport:
        end_date = end_date - timedelta(days=1)
    start_date = date2tdate(start_date)
    end_date = date2tdate(end_date)
    data_list = await get_portfolio_yield_trend(conn, portfolio, start_date, end_date)
    data = {"portfolio": portfolio, "data_list": data_list}
    return data


async def get_account_asset(
    conn: AsyncIOMotorClient,
    portfolio_id: PyObjectId,
    refresh: bool = False,
) -> Union[dict, None]:
    """账户资产查询."""
    portfolio = await get_portfolio_by_id(conn, id=portfolio_id)
    if not portfolio:
        raise EntityDoesNotExist
    fund_account = portfolio.fund_account[0]
    fund_asset = await get_fund_asset(
        conn, fund_account.fundid, portfolio.category, fund_account.currency
    )
    if refresh and portfolio.category == PortfolioCategory.ManualImport:
        fund_asset = await calculate_fund_asset(conn, fund_asset)
        fund_asset_in_update = FundAccountInUpdate(**fund_asset.dict())
        await update_fund_account_by_id(conn, fund_asset.id, fund_asset_in_update)
    if portfolio.category == PortfolioCategory.ManualImport:
        await liquidation_fund_asset(conn, portfolio)
    return await db_asset2frontend(conn, fund_asset, portfolio)


async def get_account_stock_position(
    conn: AsyncIOMotorClient,
    portfolio_id: PyObjectId,
    symbol: str,
) -> Optional[dict]:
    """股票持仓查询."""
    portfolio = await get_portfolio_by_id(conn, id=portfolio_id)
    fund_account = portfolio.fund_account[0]
    position_list = await get_fund_account_position(
        conn, fund_account.fundid, portfolio.category
    )
    data = [position for position in position_list if position.symbol == symbol]
    return await db_position2frontend(data[0]) if data else {}


async def get_account_position(
    conn: AsyncIOMotorClient, portfolio: PortfolioInResponse
) -> List[Optional[dict]]:
    """账户持仓查询."""
    fund_account = portfolio.fund_account[0]
    position_list_raw = await get_fund_account_position(
        conn, fund_account.fundid, portfolio.category
    )
    position_list = []
    for position in position_list_raw:
        try:
            rv = await db_position2frontend(position)
        except (ValidationError, HQSourceError, SecurityNotFoundError):
            continue
        position_list.append(rv)
    return position_list


class PortfolioTools:
    @classmethod
    async def basic_run_data(
        cls,
        conn: AsyncIOMotorClient,
        portfolio_id: PyObjectId,
        calculation_method: ReturnYieldCalculationMethod,
    ) -> PortfolioBasicRunDataInResponse:
        """计算组合基本运行数据."""
        portfolio = await get_portfolio_by_id(conn, id=portfolio_id)
        if not portfolio:
            raise HTTPException(404, detail=f"未找到组合`{portfolio_id}`.")
        result = {
            "portfolio": portfolio,
            "profit_rate": portfolio.profit_rate,
            "rank": portfolio.rank,
            "over_percent": portfolio.over_percent,
        }
        start_date = portfolio.import_date
        end_date = get_early_morning()
        if portfolio.category == PortfolioCategory.ManualImport:
            start_date = start_date - timedelta(days=1)
            end_date = end_date - timedelta(days=1)
        start_date = date2tdate(start_date).date()
        end_date = date2tdate(end_date).date()
        result["trade_date"] = end_date
        if portfolio.create_date.date() != get_early_morning().date():
            result["profit_rate"] = await get_portfolio_profit_rate(
                conn,
                portfolio,
                start_date=start_date,
                end_date=end_date,
                calculation_method=calculation_method,
            )
            result["daily_profit_rate"] = await get_portfolio_profit_rate(
                conn,
                portfolio,
                start_date=FastTdate.last_tdate(end_date),
                end_date=end_date,
                calculation_method=calculation_method,
            )
            result["weekly_profit_rate"] = await get_portfolio_profit_rate(
                conn,
                portfolio,
                start_date=get_date_by_type(DateType.WEEK).date(),
                end_date=end_date,
                calculation_method=calculation_method,
            )
            result["monthly_profit_rate"] = await get_portfolio_profit_rate(
                conn,
                portfolio,
                start_date=get_date_by_type(DateType.MONTH).date(),
                end_date=end_date,
                calculation_method=calculation_method,
            )
        else:
            result["profit_rate"] = 0
            result["daily_profit_rate"] = 0
            result["weekly_profit_rate"] = 0
            result["monthly_profit_rate"] = 0

        result["expected_profit_rate"] = portfolio.config.expected_return
        fund_account = await get_fund_asset(
            conn,
            fund_id=portfolio.fund_account[0].fundid,
            category=portfolio.category,
            currency=portfolio.fund_account[0].currency,
        )
        # 若今日时点数据还未准备完毕，则用上一日数据
        if date2datetime(end_date) > fund_account.ts_data_sync_date:
            end_date = FastTdate.last_tdate(end_date)
        # 最新时点评估数据
        assessment = await get_portfolio_assessment_time_series_data(
            conn, portfolio=portfolio.id, tdate=end_date
        )
        # 若没有查询到时点评估数据，则组合为今日刚创建的组合，annual_rate为0
        if not assessment:
            annual_rate = 0
        else:
            annual_rate = assessment[0].annual_rate
        if annual_rate > 0:
            days = ceil(portfolio.config.expected_return * 365 / annual_rate)
            try:
                expected_reach_date = datetime.strptime(
                    shift_trade_day(str_of_today(), days), "%Y%m%d"
                ).date()
            except NeedUpdateError:
                expected_reach_date = (
                    get_early_morning() + timedelta(days=days)
                ).date()
        else:
            expected_reach_date = None
        result["expected_reach_date"] = expected_reach_date
        return PortfolioBasicRunDataInResponse(**result)

    @classmethod
    async def get_position(cls, conn: AsyncIOMotorClient, portfolio_id: PyObjectId):
        """组合持仓信息"""
        data = {"portfolio": None, "industry_info": None, "cash": 0}
        portfolio = await get_portfolio_by_id(conn, id=portfolio_id)
        data["portfolio"] = portfolio
        fund_account = portfolio.fund_account[0]
        position_list_raw = await get_fund_account_position(
            conn, fund_account.fundid, portfolio.category
        )
        position_list = []
        for position in position_list_raw:
            try:
                rv = await db_position2frontend(position)
            except (ValidationError, HQSourceError, SecurityNotFoundError):
                continue
            position_list.append(rv)
        fund_asset = await get_fund_asset(
            conn,
            fund_id=fund_account.fundid,
            category=portfolio.category,
            currency=fund_account.currency,
        )
        industry_info = []
        industry_list = list(set([x.get("industry") for x in position_list]))
        industry_list.sort()
        for industry in industry_list:
            tmp_dict = {"name": industry}
            tmp_stocks = [x for x in position_list if x.get("industry") == industry]
            tmp_dict["stocks"] = tmp_stocks
            position = (
                sum([x.get("market_value", 0) for x in tmp_stocks])
                / fund_asset.assets.to_decimal()
            )
            tmp_dict["position"] = position
            industry_info.append(tmp_dict)
        data["industry_info"] = industry_info
        if fund_asset.cash.to_decimal() > 0:
            data["cash"] = fund_asset.cash.to_decimal() / fund_asset.assets.to_decimal()
        else:
            data["cash"] = 0
        return data

    @classmethod
    async def count(cls, conn: AsyncIOMotorClient, username: str):
        """用户未关闭状态组合数量"""
        return await get_portfolio_collection(conn).count_documents(
            {"username": username, "status": 组合状态.running.value}
        )

    @classmethod
    async def check_join_activity(
        cls, conn: AsyncIOMotorClient, username: str, activity_id: PyObjectId
    ):
        """用户未关闭状态参加活动组合数量"""
        return await get_portfolio_collection(conn).count_documents(
            {
                "username": username,
                "activity": activity_id,
                "status": 组合状态.running.value,
            }
        )

    @classmethod
    async def get_stock_risk_level(
        cls, conn: AsyncIOMotorClient, robot: dict, stock: dict
    ):
        """获取组合持仓股票风险等级."""
        start = end = (
            str_of_today()
            if FastTdate.is_tdate(str_of_today())
            else FastTdate.last_tdate(str_of_today())
        )
        if start == str_of_today() and datetime.now().hour < 19:
            start = end = FastTdate.last_tdate(start)
        equipment_dict = {x: await 查询某个装备的详情(conn, x) for x in robot["风控装备列表"]}
        grade_list = []
        for sid in robot["风控装备列表"]:
            try:
                df = get_strategy_signal(sid, start, end)
                grade = df[df["symbol"].isin([stock["symbol"]])].iloc[-1]["grade"]
            except (IndexError, KeyError):
                continue
            if grade in ["高风险", "低风险"]:
                grade_list.append({"grade": grade, "reason": equipment_dict[sid].策略话术})
        return grade_list


async def create_portfolio_service(
    conn: AsyncIOMotorClient, portfolio: PortfolioInCreate, user: User
) -> Portfolio:
    """创建组合."""
    portfolio_id = PyObjectId()
    close_date = datetime.utcnow() + timedelta(days=portfolio.config.max_period)
    if portfolio.category == PortfolioCategory.SimulatedTrading:
        fund_account = await generate_simulation_account(
            str(portfolio_id), portfolio.initial_funding
        )
    else:
        fund_account_in_db = FundAccountInDB(
            capital=portfolio.initial_funding,
            ts_data_sync_date=FastTdate.last_tdate(datetime.today()),
            assets=portfolio.initial_funding,
            cash=portfolio.initial_funding,
        )
        fund_account = await create_fund_account(conn, fund_account_in_db)
        fund_account = 用户资金账户信息(
            fundid=str(fund_account.id), create_date=fund_account.created_at
        )
    portfolio_in_db = Portfolio(
        id=portfolio_id,
        username=user.username,
        close_date=close_date,
        fund_account=[fund_account],
        import_date=FastTdate.last_tdate(datetime.today()),
        **portfolio.dict(),
    )
    robot = await 查询某机器人信息(conn, portfolio.robot, show_detail=False)
    title = (
        f"{user.nickname or user.username}({portfolio_in_db.create_date.strftime('%Y-%m-%d %H:%M:%S')}) "
        f"刚刚创建了一个新的组合:{portfolio.name} 使用的{robot.名称} 机器人."
    )
    try:
        article_category = settings.discuzq.category["组合"]
    except KeyError:
        article_category = None
    data = {
        "title": title,
        "raw": f"{title}\n{portfolio.introduction}",
        "category": article_category,
    }
    article = await create_thread(portfolio_in_db.username, **data)
    portfolio_in_db.article_id = article["id"]
    return await create_portfolio(conn, portfolio_in_db, reset_id=False)
