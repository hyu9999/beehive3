from datetime import date, timedelta
from decimal import Decimal
from typing import List, Union

from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app.crud.base import (
    get_portfolio_collection,
    get_portfolio_target_conf_collection,
    get_user_collection,
)
from app.crud.time_series_data import (
    get_portfolio_assessment_time_series_data,
)
from app.enums.portfolio import PortfolioCategory, ReturnYieldCalculationMethod, 组合状态
from app.models.base.user import 指标配置
from app.models.fund_account import FundAccountInDB
from app.models.portfolio import Portfolio
from app.models.target_config import PortfolioTargetConf
from app.models.time_series_data import (
    PortfolioAssessmentTimeSeriesDataInDB,
)
from app.schema.user import TargetDataInResponse, User, UserPortfolioTargetInResponse
from app.service.datetime import get_early_morning
from app.service.fund_account.fund_account import get_fund_asset
from app.service.portfolio.portfolio import get_portfolio_profit_rate
from app.utils.datetime import date2tdate, date2datetime


async def get_code_data(
    conn: AsyncIOMotorClient,
    code: str,
    portfolio: Portfolio,
    assessment: PortfolioAssessmentTimeSeriesDataInDB,
    fund_asset: FundAccountInDB,
    start_date: date,
    end_date: date,
) -> float:
    """获取用户组合指标数据."""
    rv = 0.0
    profit_rate = await get_portfolio_profit_rate(
        conn, portfolio, start_date, end_date, ReturnYieldCalculationMethod.SWR
    )
    profit = fund_asset.assets.to_decimal() * Decimal(profit_rate)
    profit_rate_day = await get_portfolio_profit_rate(
        conn,
        portfolio,
        FastTdate.last_tdate(end_date),
        end_date,
        ReturnYieldCalculationMethod.SWR,
    )
    profit_day = fund_asset.assets.to_decimal() * Decimal(profit_rate_day)
    if code == "10001":
        rv = profit_day
    elif code == "10002":
        rv = fund_asset.assets.to_decimal()
    elif code == "10003":
        rv = fund_asset.securities.to_decimal()
    elif code == "10004":
        rv = fund_asset.cash.to_decimal()
    elif code == "10005":
        rv = fund_asset.cash.to_decimal()
    elif code == "10006":
        rv = Decimal(profit_rate_day)
    elif code == "10007":
        rv = Decimal(profit_rate)
    elif code == "10008":
        rv = profit
    else:
        if code == "10009":
            rv = assessment.profit_loss_ratio
        elif code == "10010":
            rv = assessment.winning_rate
        elif code == "10011":
            rv = assessment.annual_rate
        elif code == "10012":
            rv = assessment.max_drawdown
        elif code == "10013":
            rv = assessment.sharpe_ratio
        elif code == "10014":
            rv = assessment.mktval_volatility
    if isinstance(rv, Decimal):
        rv = float(round(rv, 4))
    return rv


class PortfolioTargetTools:
    """组合指标"""

    @staticmethod
    async def get_config(conn: AsyncIOMotorClient, user: User):
        """获取用户配置"""
        if not user.target_config.portfolio_target:
            rows = get_portfolio_target_conf_collection(conn).find(
                {"name": {"$in": ["总收益", "总收益率"]}}
            )
            portfolio_target = [PortfolioTargetConf(**row).dict() async for row in rows]
            # 此操作会重置target_config，重置后target_config中只有portfolio_target，不能直接写入数据库
            user.target_config = 指标配置(**{"portfolio_target": portfolio_target})
            # 更新数据库，使用"target_config.portfolio_target"，不论target_config是否存在，不会重置target_config，仅更新target_config下portfolio_target字段
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"target_config.portfolio_target": portfolio_target}},
            )
        return user.target_config.portfolio_target

    @classmethod
    async def get_row_data(
        cls,
        conn: AsyncIOMotorClient,
        code_or_list: Union[List[str], str],
        portfolio: Portfolio,
    ) -> Union[List[float], float]:
        """获取用户组合指标数据"""
        start_date = portfolio.import_date
        end_date = get_early_morning()
        if portfolio.category == PortfolioCategory.ManualImport:
            start_date = start_date - timedelta(days=1)
            end_date = end_date - timedelta(days=1)
        start_date = date2tdate(start_date).date()
        end_date = date2tdate(end_date).date()
        fund_account = portfolio.fund_account[0]
        fund_asset = await get_fund_asset(
            conn, fund_account.fundid, portfolio.category, fund_account.currency
        )
        assessment = await get_portfolio_assessment_time_series_data(
            conn, portfolio=portfolio.id
        )
        if not assessment:
            assessment = [PortfolioAssessmentTimeSeriesDataInDB(
                portfolio=portfolio.id,
                tdate=date2datetime(end_date),
            )]
        if isinstance(code_or_list, list):
            rv = []
            for code in code_or_list:
                rv.append(
                    await get_code_data(
                        conn,
                        code,
                        portfolio,
                        assessment[-1],
                        fund_asset,
                        start_date,
                        end_date,
                    )
                )
        else:
            rv = await get_code_data(
                conn,
                code_or_list,
                portfolio,
                assessment[-1],
                fund_asset,
                start_date,
                end_date,
            )
        return rv

    @classmethod
    async def _get_data(
        cls, conn: AsyncIOMotorClient, portfolio: Portfolio, user: User
    ):
        """获取数据"""
        configs = await cls.get_config(conn, user)
        return [
            {
                "name": config.name,
                "value": await cls.get_row_data(conn, config.code, portfolio),
            }
            for config in configs
        ]

    @classmethod
    async def get_data_list(
        cls, conn: AsyncIOMotorClient, portfolio_list: List[Portfolio], user: User
    ) -> List[UserPortfolioTargetInResponse]:
        """获取数据列表"""
        return [
            UserPortfolioTargetInResponse(
                **{
                    "portfolio": portfolio,
                    "user": user,
                    "data": await cls._get_data(conn, portfolio, user),
                }
            )
            for portfolio in portfolio_list
        ]

    @classmethod
    async def get_user_target_data(
        cls,
        conn: AsyncIOMotorClient,
        code_list: List[str],
        portfolio: Portfolio,
    ):
        data = await cls.get_row_data(conn, code_list, portfolio)
        return TargetDataInResponse(data_list=data)


# TODO 添加缓存
async def get_user_portfolio_targets(
    conn: AsyncIOMotorClient, user: User
) -> List[UserPortfolioTargetInResponse]:
    """获取用户组合指标"""
    rows = get_portfolio_collection(conn).find(
        {
            "status": 组合状态.running.value,
            "$or": [
                {"_id": {"$in": user.portfolio.subscribe_info.focus_list}},
                {"username": user.username},
            ],
        }
    )
    portfolio_list = [Portfolio(**row) async for row in rows]
    data = await PortfolioTargetTools.get_data_list(conn, portfolio_list, user)
    return data
