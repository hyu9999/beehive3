from datetime import date, datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pandas import DataFrame
from stralib import FastTdate, get_strategy_signal

from app.crud.base import (
    get_equipment_collection,
    get_portfolio_collection,
    get_robots_collection,
)
from app.crud.portfolio import get_portfolio_by_id
from app.enums.portfolio import 风险点状态, 风险类型
from app.extentions import logger
from app.models.base.portfolio import 风险点信息
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.outer_sys.hq import get_security_info
from app.schema.portfolio import PortfolioInResponse
from app.schema.signal import (
    ScreenStrategySignalInResponse,
    TimingStrategySignalInResponse,
    TradeStrategySignalInResponse,
    TradeStrategySignalInfo,
)
from app.service.check_status import CheckStatus
from app.service.equipment import format_trade_equipment_strategy_word
from app.service.fund_account.fund_account import get_fund_account_position
from app.utils.market_convert import MarketConverter


def get_signal_date(search_date: date) -> date:
    """
    根据传入的日期获取实际出信号的日期
    Parameters
    ----------
    search_date 查询日期

    Returns
    -------
    实际出信号的日期
    """
    if not FastTdate.is_tdate(search_date):
        search_date = FastTdate.last_tdate(search_date)
    elif search_date == date.today() and datetime.now().hour < 19:
        search_date = FastTdate.last_tdate(search_date)
    return search_date


def select_column_tolist(df, *cols):
    """
    筛选df中指定columns列表
    Parameters
    ----------
    df  待筛选DataFrame
    cols 筛选列名

    Returns
    -------

    """
    return [getattr(df, col).tolist() for col in cols]


async def screen_strategy_signal_list(conn: AsyncIOMotorClient, portfolio_id: PyObjectId, signal_date: date) -> List[ScreenStrategySignalInResponse]:
    """
    获取某日某组合的选股装备对应的策略信号列表
    Parameters
    ----------
    conn 数据库连接
    portfolio_id  组合id
    signal_date  信号日期

    Returns
    -------
    List[StockScreenSignalInResponse]
    """

    portfolio = await get_portfolio_collection(conn).find_one({"_id": portfolio_id})
    robot = await get_robots_collection(conn).find_one({"标识符": portfolio["robot"]})
    stock_equips = robot["选股装备列表"]

    res_list = []
    for sid in stock_equips:
        signals = get_strategy_signal(sid, signal_date.strftime("%Y%m%d"), signal_date.strftime("%Y%m%d"))
        # 去掉股票代码为‘nan’的信号（股票代码为‘nan’表示当日信号已运行，但是无信号）
        signals = signals[signals.SYMBOL != "nan"].dropna(subset=["SYMBOL"]) if not signals.empty else signals
        if signals.empty:
            logger.warning(f"{signal_date} 该日选股策略: {sid} 无信号")
            continue

        signals.reset_index(drop=True, inplace=True)
        signals.replace({"EXCHANGE": MarketConverter.STRALIB_EXCHANGE_MAPPER}, inplace=True)
        signals.rename(
            columns={
                "SYMBOL": "symbol",
                "EXCHANGE": "exchange",
                "TCLOSE": "chosen_price",
            },
            inplace=True,
        )
        selected = select_column_tolist(signals, "symbol", "exchange")
        descriptions = []
        for symbol, exchange in zip(*selected):
            security = await get_security_info(symbol, exchange)
            data = security.dict()
            data["exchange"] = "1" if security.exchange == "SH" else "0"
            descriptions.append(data)
        df = DataFrame(descriptions)
        try:
            intact_signals = signals.merge(df, how="outer", on=["symbol", "exchange"])
        except:
            logger.warning(f"{signal_date} 该日选股策略: {sid} 无信号")
            continue
        equipment = await get_equipment_collection(conn).find_one({"标识符": sid})
        stocks = [s for s in intact_signals.to_dict("records")]
        for stock in stocks:
            stock["chosen_reason"] = equipment.get("策略话术")
        res_list.append(
            ScreenStrategySignalInResponse(
                **{
                    "signal_date": signal_date,
                    "equipment": equipment,
                    "strategy_signals": stocks,
                }
            )
        )
    return res_list


def format_stralib_timing_signal(sid: str, symbol: str, start_date: str, end_date: str) -> List[TimingStrategySignalInResponse]:
    """
    格式化stralib调用返回的择时信号
    Parameters
    ----------
    sid 择时装备标识符
    symbol 股票代码
    start_date 开始日期，"%Y%m%d"
    end_date  结束日期，"%Y%m%d"
    Returns
    -------
    List[TimingStrategySignalInResponse]
    """
    signal = get_strategy_signal(sid, start_date, end_date)
    ret_data = []
    if not signal.empty:
        for item in signal.T.to_dict().values():
            trend = item[f"market_trend_shape_{symbol}"]
            base_advice = item[f"position_rate_advice_{symbol}"]
            tmp_dict = {
                "trade_date": datetime.strptime(item["TDATE"], "%Y%m%d"),
                "market_trend": trend,
                "position_rate_advice": [
                    base_advice.split("-")[0],
                    base_advice.split("-")[1][:-1],
                ],
                "valuation_quantile": item.get(f"valuation_quantile_{symbol}"),
            }
            ret_data.append(TimingStrategySignalInResponse(**tmp_dict))
    return ret_data


async def timing_strategy_signal_list(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    symbol: str,
    start_date: date,
    end_date: date,
) -> List[TimingStrategySignalInResponse]:
    """择时列表"""
    robot = await get_robots_collection(conn).find_one({"标识符": portfolio.robot})
    equip_sid = robot["择时装备列表"][0] if robot and robot.get("择时装备列表") else None  # 目前择时策略只有一个需要展示
    if not equip_sid:
        return []
    return format_stralib_timing_signal(equip_sid, symbol, start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))


async def timing_strategy_signal(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    start_date: date,
    end_date: date = None,
) -> Optional[TimingStrategySignalInResponse]:
    """择时信号"""
    if not end_date:
        end_date = start_date
    robot = await get_robots_collection(conn).find_one({"标识符": portfolio.robot})
    timing_sid = robot["择时装备列表"][0] if robot and robot.get("择时装备列表") else None
    if not timing_sid:
        return
    equip_status = await CheckStatus.check_equip_status_by_sid(conn, [timing_sid])
    # 当天数据未准备完毕，则显示昨天的信号
    if start_date == date.today() and not equip_status:
        start_date = FastTdate.last_tdate(start_date)
    signal_list = format_stralib_timing_signal(timing_sid, "399001", start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))
    if signal_list:
        return signal_list[0]


async def trade_strategy_signal(conn: AsyncIOMotorClient, portfolio_id: PyObjectId, signal_date: date) -> List[TradeStrategySignalInResponse]:
    """交易信号"""
    portfolio = await get_portfolio_collection(conn).find_one({"_id": portfolio_id})
    portfolio = PortfolioInResponse(**portfolio)
    fund_account = portfolio.fund_account[0]
    position_list = await get_fund_account_position(conn, fund_account.fundid, portfolio.category)
    symbol_list = [stk.symbol for stk in position_list]
    robot = await get_robots_collection(conn).find_one({"标识符": portfolio.robot})
    stock_equips = robot["交易装备列表"]

    res_list = []
    for sid in stock_equips:
        signals = get_strategy_signal(sid, signal_date.strftime("%Y%m%d"), signal_date.strftime("%Y%m%d"))
        signals = signals[signals.SYMBOL.isin(symbol_list)]
        signals = signals[signals.SIGNAL != 0.0]
        if signals.empty:
            logger.warning(f"{signal_date} 该日交易策略: {sid} 无信号")
            continue

        signals.reset_index(drop=True, inplace=True)
        signals.replace({"EXCHANGE": MarketConverter.STRALIB_EXCHANGE_MAPPER}, inplace=True)
        signals.rename(
            columns={
                "SYMBOL": "symbol",
                "REASON": "reason",
                "EXCHANGE": "exchange",
                "TCLOSE": "price",
                "TDATE": "date",
                "SIGNAL": "operator",
            },
            inplace=True,
        )
        selected = select_column_tolist(signals, "symbol", "exchange")
        descriptions = []
        for symbol, exchange in zip(*selected):
            security = await get_security_info(symbol, exchange)
            data = security.dict()
            data["exchange"] = "1" if security.exchange == "SH" else "0"
            descriptions.append(data)
        df = DataFrame(descriptions)
        try:
            intact_signals = signals.merge(df, how="outer", on=["symbol", "exchange"])
        except:
            logger.warning(f"{signal_date} 该日交易策略: {sid} 无信号")
            continue
        equip_obj = await get_equipment_collection(conn).find_one({"标识符": sid})
        stocks = []
        for stock in intact_signals.to_dict("records"):
            stock["title"] = get_stock_title(stock, equip_obj)
            stock["advice"] = format_trade_equipment_strategy_word(stock["reason"], equip_obj["策略话术"])
            stock["symbol_shortname"] = stock["symbol_short_name"]
            stocks.append(TradeStrategySignalInfo(**stock))
        res_list.append(TradeStrategySignalInResponse(**{"equipment": equip_obj, "strategy_signals": stocks}))
    return res_list


async def risk_strategy_signal(conn: AsyncIOMotorClient, portfolio_id: PyObjectId) -> List[风险点信息]:
    """个股风险"""
    portfolio = await get_portfolio_by_id(conn, portfolio_id)
    # 个股风险页面只展示未确认和未解决的个股风险
    risks = [
        risk
        for risk in portfolio.risks
        if risk.risk_type not in [风险类型.overweight, 风险类型.underweight, 风险类型.adjustment_cycle] and risk.status in [风险点状态.confirm, 风险点状态.unresolved]
    ]
    return risks


def get_stock_title(stock, equip_obj):
    """拼装个股买卖标题"""
    reason = "看多" if stock.get("operator") == 1 else "看空"
    content = f'"{stock.get("symbol_name")}"{equip_obj.get("名称")}指标出现{reason}信号'
    return content
