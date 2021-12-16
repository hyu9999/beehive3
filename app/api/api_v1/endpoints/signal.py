from datetime import date

from fastapi import APIRouter, Security, Depends, Path, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional

from app.core.jwt import get_current_user_authorizer
from app.crud.portfolio import get_portfolio_by_id
from app.db.mongodb import get_database
from app.models.base.portfolio import 风险点信息
from app.models.rwmodel import PyObjectId
from app.schema.signal import ScreenStrategySignalInResponse, TimingStrategySignalInResponse, TradeStrategySignalInResponse
from app.service.signal import (
    get_signal_date,
    timing_strategy_signal,
    timing_strategy_signal_list,
    risk_strategy_signal,
    trade_strategy_signal,
    screen_strategy_signal_list,
)

router = APIRouter()


@router.get("/screens/{portfolio_id}", response_model=List[ScreenStrategySignalInResponse], description="选股策略信号列表")
async def screen_strategy_signal_list_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    search_date: date = Query(None, description="信号日期, 默认为查询当天的日期"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    if not search_date:
        search_date = date.today()
    signal_date = get_signal_date(search_date)
    return await screen_strategy_signal_list(db, portfolio_id, signal_date)


@router.get("/timings/{portfolio_id}", response_model=List[TimingStrategySignalInResponse], description="择时策略信号列表")
async def timing_signal_list_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    symbol: str = Query("399001", regex="^[0-9]{6}$", description="股票代码，必须是6为0-9数字组成"),
    start_date: date = Query(None, description="开始日期"),
    end_date: date = Query(None, description="结束日期"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    start_date = start_date or date.today()
    end_date = end_date or date.today()
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    return await timing_strategy_signal_list(db, portfolio, symbol, start_date, end_date)


@router.get("/timing/{portfolio_id}", response_model=Optional[TimingStrategySignalInResponse], description="择时策略信号")
async def timing_signal_get_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    signal_date = get_signal_date(date.today())
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    return await timing_strategy_signal(db, portfolio, signal_date)


@router.get("/risks/{portfolio_id}", response_model=List[风险点信息], description="个股风险信号列表")
async def risk_signal_list_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    return await risk_strategy_signal(db, portfolio_id)


@router.get("/trades/{portfolio_id}", response_model=List[TradeStrategySignalInResponse], description="交易策略信号列表")
async def trade_signal_list_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    signal_date = get_signal_date(date.today())
    return await trade_strategy_signal(db, portfolio_id, signal_date)
