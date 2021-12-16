from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

from app.crud.base import get_activity_collection, get_portfolio_collection
from app.enums.portfolio import 组合状态
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.service.portfolio.portfolio import get_portfolio_profit_rate


async def join_activity(conn: AsyncIOMotorClient, activity_id: PyObjectId, username: str):
    """
    参加活动
    参加活动规则：一个用户只允许参加一次；不允许结束该组合
    """
    result = await get_activity_collection(conn).update_one({"_id": activity_id}, {"$addToSet": {"participants": username}})
    return result


async def cal_portfolio_ranking_in_activity_by_date(conn: AsyncIOMotorClient, activity_id: ObjectId, cal_date: datetime):
    """
    根据日期计算参加活动的所有组合的排名信息

    Parameters
    ----------
    conn
    activity_id
    cal_date

    Returns
    -------

    """
    portfolio_list = get_portfolio_collection(conn).find({"status": 组合状态.running, "activity": activity_id})
    profit_list = []
    # 获取各个组合收益并排序
    async for portfolio in portfolio_list:
        profit_rate = await get_portfolio_profit_rate(Portfolio(**portfolio.dict()), portfolio["create_date"], cal_date)
        profit_list.append(
            {
                "activity": activity_id,
                "portfolio": portfolio["_id"],
                "portfolio_name": portfolio["name"],
                "profit_rate": profit_rate,
            }
        )
    profit_list.sort(key=lambda x: x["profit_rate"], reverse=True)
    profit_list_len = len(profit_list)
    # 根据组合收益计算排名等信息
    replace_list = []
    for index, profit_info in enumerate(profit_list):
        portfolio_id = profit_info["portfolio"]
        profit_info["rank"] = index + 1
        profit_info["over_percent"] = 1 - (profit_info["rank"] - 1) / profit_list_len
        defaults = {"activity": str(activity_id), "portfolio": portfolio_id}
        replace_list.append(UpdateOne(defaults, {"$set": profit_info}, upsert=True))
    return replace_list
