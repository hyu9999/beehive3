from collections import defaultdict
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_stock_stats_conf_collection, get_user_collection
from app.enums.fund_account import FlowTType
from app.enums.portfolio import PortfolioCategory
from app.models.base.portfolio import 用户资金账户信息
from app.models.base.user import 指标配置
from app.models.portfolio import Portfolio
from app.models.target_config import StockStatsConf
from app.outer_sys.hq import get_security_hq
from app.schema.user import User
from app.service.datetime import get_early_morning
from app.service.fund_account.fund_account import (
    get_fund_account_flow,
    get_fund_account_position,
)
from app.utils.exchange import convert_exchange


class StockStatisticsTools:
    """个股统计"""

    @classmethod
    async def get_config(cls, conn: AsyncIOMotorClient, user: User):
        """获取用户个股统计配置"""
        if not user.target_config.stock_stats:
            rows = get_stock_stats_conf_collection(conn).find({})
            stock_stats = [StockStatsConf(**row).dict() async for row in rows][:2]
            # 此操作会重置target_config，重置后target_config中只有stock_stats，不能直接写入数据库
            user.target_config = 指标配置(**{"stock_stats": stock_stats})
            # 更新数据库，使用"target_config.stock_stats"，不论target_config是否存在，不会重置target_config，仅更新target_config下stock_stats字段
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"target_config.stock_stats": stock_stats}},
            )
        return user.target_config.stock_stats

    @classmethod
    async def _get_data(
        cls,
        conn: AsyncIOMotorClient,
        portfolio: Portfolio,
        start_date: datetime,
        end_date: datetime,
    ):
        """获取数据"""
        fund_account = portfolio.fund_account[0]
        position_list = await get_fund_account_position(
            conn, fund_account.fundid, portfolio.category
        )
        position_dict = {position.symbol: position for position in position_list}
        flow_list = await get_fund_account_flow(
            conn, fund_account.fundid, portfolio.category, fund_account.currency
        )
        if portfolio.category == PortfolioCategory.ManualImport:
            flow_list = [
                flow for flow in flow_list if flow.created_at < get_early_morning()
            ]
        if not flow_list:
            return []
        start_date = start_date or min([flow.tdate for flow in flow_list])
        flow_group = defaultdict(list)
        for flow in flow_list:
            flow_group[flow.symbol].append(flow)
        ret_list = []
        for symbol, group in flow_group.items():
            if symbol not in position_dict.keys():
                continue
            position = position_dict[symbol]
            tmp_dict = {"symbol": symbol}
            security = await get_security_hq(
                symbol=symbol,
                exchange=convert_exchange(position.exchange, to="beehive"),
            )
            tmp_dict["symbol_name"] = security.symbol_name
            tmp_data = [
                {
                    "name": "收益",
                    "value": (security.current - position.cost.to_decimal())
                    * position.volume,
                },
                {
                    "name": "交易次数",
                    "value": await get_trade_num(
                        conn, fund_account, start_date, end_date, symbol, portfolio
                    ),
                },
            ]
            tmp_dict["data"] = tmp_data
            ret_list.append(tmp_dict)
        return ret_list

    @classmethod
    async def get_data(
        cls,
        conn: AsyncIOMotorClient,
        portfolio: Portfolio,
        start_date: datetime,
        end_date: datetime,
    ):
        """获取数据"""
        data = await cls._get_data(conn, portfolio, start_date, end_date)
        return data


async def get_trade_num(
    conn: AsyncIOMotorClient,
    fund_account: 用户资金账户信息,
    start_date: datetime,
    end_date: datetime,
    symbol: str,
    portfolio: Portfolio,
):
    """获取交易次数"""
    flow_list = await get_fund_account_flow(
        conn,
        fund_account.fundid,
        portfolio.category,
        fund_account.currency,
        start_date=start_date.date(),
        end_date=end_date.date(),
    )
    return len(
        [
            flow
            for flow in flow_list
            if flow.ttype == FlowTType.SELL and flow.symbol == symbol
        ]
    )
