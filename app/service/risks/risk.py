from datetime import date, datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate, Robot

from app.crud.base import get_portfolio_collection
from app.crud.portfolio import get_portfolio_list, update_portfolio_by_id
from app.db.mongodb import db
from app.enums.portfolio import 组合状态, 风险点状态, 风险类型
from app.enums.solution import SolutionStepEnum
from app.models.base.portfolio import 风险点信息
from app.models.fund_account import FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.schema.portfolio import PortfolioInUpdate
from app.service.fund_account.fund_account import (
    get_fund_account_position,
    get_fund_asset,
)
from app.service.signal import timing_strategy_signal


async def get_position_risks_step(
    portfolio: Portfolio, robot: Robot
) -> Optional[SolutionStepEnum]:
    """获取仓位风险类型"""
    robot.get_hold_risk()
    robot.check_position()
    adviced_range = [
        float(robot.timing_signal.split("-")[0]) / 100,
        float(robot.timing_signal.split("-")[1][:-1]) / 100,
    ]
    ignored_risks_type = list(set([x.risk_type for x in portfolio.get_ignore_risks()]))
    step = None
    # 仓位过轻
    if robot.current_position < adviced_range[0]:
        if 风险类型.underweight not in ignored_risks_type:
            step = SolutionStepEnum.UNDERWEIGHT
    # 仓位过重
    elif robot.current_position > adviced_range[1]:
        if 风险类型.overweight not in ignored_risks_type:
            step = SolutionStepEnum.OVERWEIGHT
    return step


async def get_sl_tp_risks(portfolio: Portfolio) -> List[风险点信息]:
    """获取组合中的止盈止损风险"""
    user_accepted_risks = [
        risk
        for risk in portfolio.risks
        if risk.status == 风险点状态.confirmed
        and risk.risk_type
        not in [风险类型.overweight, 风险类型.underweight, 风险类型.clearance_line]
    ]
    return user_accepted_risks


async def finish_portfolio_risks():
    """重置所有组合风险"""
    running_portfolio = await get_portfolio_list(db.client, {"status": 组合状态.running})
    for portfolio in running_portfolio:
        for risk in portfolio.risks:
            risk.status = 风险点状态.resolved
        await update_portfolio_by_id(
            db.client, portfolio.id, PortfolioInUpdate(**dict(portfolio))
        )


async def get_all_risks(
    conn: AsyncIOMotorClient, portfolio_id: PyObjectId, show_all: bool
) -> List[风险点信息]:
    """获取全部风险"""
    ret_risk = []
    db_portfolio = await get_portfolio_collection(conn).find_one({"_id": portfolio_id})
    portfolio = Portfolio(**db_portfolio)
    risk_date = date.today()
    if FastTdate.is_tdate(risk_date) and not portfolio.risks:
        return ret_risk
    fund_account = portfolio.fund_account[0]
    stocks = await get_fund_account_position(
        conn, fund_account.fundid, portfolio.category
    )
    await ignore_abnormal_risks(conn, portfolio, stocks)
    if show_all:
        risks = portfolio.risks
    else:
        risks = [
            risk
            for risk in portfolio.risks
            if risk.status in [风险点状态.confirm, 风险点状态.confirmed, 风险点状态.solving]
        ]
    if not risks:
        return risks
    assets = await get_fund_asset(
        conn, fund_account.fundid, portfolio.category, fund_account.currency
    )
    position_rate = assets.securities.to_decimal() / assets.assets.to_decimal()
    data = await timing_strategy_signal(conn, portfolio, risk_date)
    position_advice = data.position_rate_advice
    for risk in risks:
        if risk.risk_type in [风险类型.overweight, 风险类型.underweight, 风险类型.adjustment_cycle]:
            risk.position_rate = position_rate
            risk.position_advice = position_advice
        ret_risk.append(risk)
    return ret_risk


async def ignore_abnormal_risks(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    stocks: List[FundAccountPositionInDB],
):
    """将异常风险置为无效"""
    # 持仓股票代码和持仓量列表,但触发该风险的股票已经不在持仓里，则将该风险修改为已忽略的状态
    symbol_dict = {stk.symbol: stk.volume for stk in stocks}
    # 持仓股票代码和可用数量，如果可用数量为零则修改该风险状态为已忽略的状态
    available_symbol_dict = {stk.symbol: stk.available_volume for stk in stocks}
    for risk in portfolio.risks:  # 所有触发的个股风险仍然拥有该个股风险的持仓
        if not risk.symbol:
            continue
        if risk.symbol not in symbol_dict:
            risk.status = 风险点状态.ignored
        elif symbol_dict.get(risk.symbol) == 0:
            risk.status = 风险点状态.ignored
        elif available_symbol_dict.get(risk.symbol) == 0:
            risk.status = 风险点状态.ignored
    portfolio.updated_at = datetime.utcnow()
    await get_portfolio_collection(conn).update_one(
        {"_id": portfolio.id}, {"$set": portfolio.dict(include={"risks", "updated_at"})}
    )
