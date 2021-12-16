from motor.motor_asyncio import AsyncIOMotorClient

from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.outer_sys.hq import get_security_hq
from app.service.datetime import get_early_morning
from app.service.fund_account.fund_account import (
    calculation_simple,
    get_net_deposit_flow,
)
from app.service.time_series_data.time_series_data import get_assets_time_series_data
from app.utils.datetime import date2tdate
from app.utils.exchange import convert_exchange


async def db_position2frontend(position: FundAccountPositionInDB) -> dict:
    """数据库中持仓格式转换为前端所需要的格式."""
    exchange = convert_exchange(position.exchange, to="beehive")
    security = await get_security_hq(symbol=position.symbol, exchange=exchange)
    return {
        "buy_price": position.cost.to_decimal(),
        "exchange": exchange,
        "symbol": position.symbol,
        "symbol_name": security.symbol_name,
        "stock_quantity": position.volume,
        "stock_available_quantity": position.available_volume,
        "industry": security.industry,
        "current": security.current,
        "market_value": security.current * position.volume,
    }


async def db_asset2frontend(
    conn: AsyncIOMotorClient, fund_asset: FundAccountInDB, portfolio: Portfolio
) -> dict:
    """数据库中资产格式转换为前端所需要的格式."""
    current_date = get_early_morning()
    start_date = date2tdate(portfolio.import_date).date()
    end_date = date2tdate(current_date).date()
    assets_list = await get_assets_time_series_data(
        conn, portfolio, start_date, end_date
    )
    net_deposit_list = await get_net_deposit_flow(
        conn, portfolio, start_date, end_date, include_capital=False, include_today=True
    )
    if assets_list.empty:
        profit_rate = 0
        profit = 0
    else:
        profit_rate = calculation_simple(net_deposit_list, assets_list)
        profit = profit_rate * assets_list[0]
    return {
        "fund_available": fund_asset.cash.to_decimal(),
        "fund_depositable": fund_asset.cash.to_decimal(),
        "market_value": fund_asset.securities.to_decimal(),
        "total_capital": fund_asset.assets.to_decimal(),
        "total_profit": profit,
        "total_profit_rate": profit_rate,
    }
