from datetime import date, datetime

import numpy as np
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app.crud.time_series_data import (
    create_fund_time_series_data,
    create_portfolio_assessment_time_series_data,
    create_position_time_series_data,
    get_fund_time_series_data,
)
from app.models.portfolio import Portfolio
from app.models.time_series_data import (
    FundTimeSeriesDataInDB,
    PortfolioAssessmentTimeSeriesDataInDB,
    PositionTimeSeriesDataInDB,
)
from app.service.fund_account.fund_account import get_fund_asset
from app.service.time_series_data.converter import fund2time_series
from app.utils.datetime import date2datetime


async def get_assets_time_series_data(
    conn: AsyncIOMotorClient, portfolio: Portfolio, start_date: date, end_date: date
) -> pd.Series:
    """获取组合持仓市值时点数据."""
    fund_account = portfolio.fund_account[0]
    assets_time_series_data_list = await get_fund_time_series_data(
        conn, fund_id=fund_account.fundid, start_date=start_date, end_date=end_date
    )
    if end_date == datetime.today().date():
        fund_assets = await get_fund_asset(
            conn, fund_account.fundid, portfolio.category, fund_account.currency
        )
        assets_time_series_data_list.append(
            fund2time_series(fund_assets, date2datetime(end_date))
        )
    assets_raw = {
        i.tdate.date(): i.mktval.to_decimal() + i.fundbal.to_decimal()
        for i in assets_time_series_data_list
    }
    return pd.Series(assets_raw, dtype=np.float64, name="股票资产")


async def create_init_time_series_data(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
) -> None:
    """创建初始时点数据."""
    fund_account = portfolio.fund_account[0]
    tdate = FastTdate.last_tdate(datetime.today())
    fund_time_series_data = FundTimeSeriesDataInDB(
        fund_id=fund_account.fundid,
        tdate=tdate,
        fundbal=portfolio.initial_funding,
        mktval=0,
    )
    await create_fund_time_series_data(conn, fund_time_series_data)

    position_time_series_data = PositionTimeSeriesDataInDB(
        fund_id=fund_account.fundid,
        tdate=tdate,
    )
    await create_position_time_series_data(conn, position_time_series_data)

    portfolio_assessment_time_series_data = PortfolioAssessmentTimeSeriesDataInDB(
        portfolio=portfolio.id, tdate=tdate
    )
    await create_portfolio_assessment_time_series_data(
        conn, portfolio_assessment_time_series_data
    )
