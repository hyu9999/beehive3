import asyncio
from datetime import datetime, timedelta

from pymongo import UpdateOne

from app import settings
from app.core.errors import EntityDoesNotExist
from app.crud.base import get_portfolio_collection
from app.db.mongodb import db
from app.enums.portfolio import PortfolioCategory, 组合状态
from app.extentions import logger
from app.models.portfolio import Portfolio
from app.service.datetime import get_early_morning
from app.service.fund_account.fund_account import (
    calculation_simple,
    get_net_deposit_flow,
)
from app.service.time_series_data.time_series_data import get_assets_time_series_data
from app.utils.datetime import date2tdate


async def update_portfolio_profit_rank_data():
    """
    更新组合总收益排行数据
    """
    while True:
        logger.debug(f"【start】更新组合总收益排行")
        portfolio_list = get_portfolio_collection(db.client).find(
            {"status": 组合状态.running}
        )
        profit_list = []
        async for portfolio in portfolio_list:
            portfolio = Portfolio(**portfolio)
            start_date = portfolio.import_date
            end_date = get_early_morning()
            if portfolio.category == PortfolioCategory.ManualImport:
                start_date = start_date - timedelta(days=1)
                end_date = end_date - timedelta(days=1)
            start_date = date2tdate(start_date)
            end_date = date2tdate(end_date)
            try:
                assets_list = await get_assets_time_series_data(
                    db.client, portfolio, start_date, end_date
                )
                net_deposit_list = await get_net_deposit_flow(
                    db.client, portfolio, start_date, end_date, include_capital=False
                )
            except EntityDoesNotExist:
                logger.warning(f"组合`{portfolio.id}`资金账户不存在, 已跳过.")
                continue
            if (
                assets_list.empty
                or portfolio.create_date.date() == get_early_morning().date()
            ):
                rate = 0
            else:
                rate = calculation_simple(net_deposit_list, assets_list)
            profit_list.append(
                {
                    "portfolio_id": portfolio.id,
                    "profit_rate": rate,
                }
            )
            await asyncio.sleep(0.1)
        profit_list.sort(key=lambda x: x["profit_rate"], reverse=True)
        profit_list_len = len(profit_list)
        update_list = [
            UpdateOne(
                {"_id": profit_info["portfolio_id"]},
                {
                    "$set": {
                        "profit_rate": profit_info["profit_rate"],
                        "rank": index + 1,
                        "over_percent": 1 - index / profit_list_len,
                    }
                },
            )
            for index, profit_info in enumerate(profit_list)
        ]
        if update_list:
            await get_portfolio_collection(db.client).bulk_write(update_list)
        await asyncio.sleep(5)
        logger.debug(f"【end】更新组合总收益排行")
        if datetime.now().time() > settings.close_market_time:
            break
