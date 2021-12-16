from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import (
    get_portfolio_assessment_time_series_data_collection,
    get_portfolio_collection,
    get_trade_stats_conf_collection,
    get_user_collection,
)
from app.crud.portfolio import get_portfolio_by_id
from app.enums.fund_account import FlowTType
from app.enums.portfolio import 组合状态
from app.models.base.user import 指标配置
from app.models.portfolio import Portfolio
from app.models.target_config import TradeStatsConf
from app.models.user import User
from app.service.fund_account.fund_account import get_fund_account_flow


class TradeStatisticsTools:
    """交易统计"""

    @staticmethod
    async def get_config(conn: AsyncIOMotorClient, username: str):
        """获取用户交易统计配置"""
        row = await get_user_collection(conn).find_one({"username": username})
        user = User(**row)
        if not user.target_config or not user.target_config.trade_stats:
            rows = get_trade_stats_conf_collection(conn).find()
            trade_stats = [TradeStatsConf(**row).dict() async for row in rows][:2]
            # 此操作会重置target_config，重置后target_config中只有trade_stats，不能直接写入数据库
            user.target_config = 指标配置(**{"trade_stats": trade_stats})
            # 更新数据库，使用"target_config.trade_stats"，不论target_config是否存在
            # 不会重置target_config，仅更新target_config下trade_stats字段
            await get_user_collection(conn).update_one(
                {"username": user.username},
                {"$set": {"target_config.trade_stats": trade_stats}},
            )
        return user.target_config.trade_stats

    @classmethod
    async def get_data(
        cls,
        conn: AsyncIOMotorClient,
        portfolio: Portfolio,
        start_date: datetime,
        end_date: datetime,
    ):
        """获取交易统计数据"""
        portfolio_list = get_portfolio_collection(conn).find(
            {"status": 组合状态.running.value}
        )
        avg_data = await cls._get_data(
            conn,
            portfolio,
            start_date,
            end_date,
            portfolio_id_list=[portfolio["_id"] async for portfolio in portfolio_list],
        )
        portfolio_data = await cls._get_data(
            conn, portfolio, start_date, end_date, portfolio_id_list=None
        )
        return {"avg_data": avg_data, "portfolio_data": portfolio_data}

    @classmethod
    async def _get_data(
        cls,
        conn: AsyncIOMotorClient,
        portfolio: Portfolio,
        start_date: datetime,
        end_date: datetime,
        portfolio_id_list: Optional[list] = None,
    ):
        """获取数据"""
        configs = await cls.get_config(conn, portfolio.username)
        if not portfolio_id_list:
            portfolio_id_list = [portfolio.id]
        rv = []
        for config in configs:
            # config.en_name en_name为beehive2 trade_stats字段 现更改为code，需保证trade_stats中code字段为英文
            tmp_dict = {
                "name": config.name,
                "value": await cls.get_row_data(
                    conn, config.code, portfolio_id_list, start_date, end_date
                ),
            }
            rv.append(tmp_dict)
        return rv

    @classmethod
    async def get_row_data(
        cls,
        conn: AsyncIOMotorClient,
        row_name: str,
        portfolio_id_list: list,
        start_date: datetime,
        end_date: datetime,
    ):
        if row_name in ["winning_rate", "profit_loss_ratio", "trade_cost"]:
            pipeline = [
                {
                    "$match": {
                        "portfolio": {"$in": portfolio_id_list},
                        "tdate": {"$gte": start_date, "$lte": end_date},
                        "trade_cost": {"$ne": 0},
                    }
                },
                {
                    "$group": {
                        "_id": {"portfolio": "$portfolio"},
                        "avg": {"$avg": f"${row_name}"},
                    }
                },
            ]
            if row_name == "trade_cost":
                pipeline[1]["$group"]["avg"] = {"$sum": f"${row_name}"}
            q_list = [
                x.get("avg", 0)
                async for x in get_portfolio_assessment_time_series_data_collection(
                    conn
                ).aggregate(pipeline)
            ]
            try:
                ret_data = sum(q_list) / len(q_list)
            except ZeroDivisionError:
                ret_data = 0
            return ret_data
        elif row_name == "trade_frequency":
            flow_list = []
            for portfolio_id in portfolio_id_list:
                portfolio = await get_portfolio_by_id(conn, portfolio_id)
                fund_account = portfolio.fund_account[0]
                flow = await get_fund_account_flow(
                    conn,
                    fund_account.fundid,
                    portfolio.category,
                    fund_account.currency,
                    start_date.date(),
                    end_date.date(),
                    [FlowTType.SELL],
                )
                flow_list.extend(flow)
            rv = len(flow_list) / len(portfolio_id_list)
            return rv
