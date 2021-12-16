from datetime import datetime, timedelta
from typing import List, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from stralib import FastTdate

from app import settings
from app.core.errors import NoPortfolioError, PortfolioCloseError
from app.crud.base import (
    get_portfolio_analysis_collection,
    get_portfolio_collection,
    get_user_collection,
    get_user_message_collection,
)
from app.crud.discuzq import create_thread
from app.crud.fund_account import create_fund_account
from app.crud.robot import 查询某机器人信息
from app.enums.portfolio import PortfolioCategory, 组合状态
from app.enums.user import 消息分类, 消息类型
from app.global_var import G
from app.models.base.portfolio import 用户资金账户信息, 风险点信息
from app.models.fund_account import FundAccountInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import PageInResponse, ResultInResponse
from app.schema.portfolio import (
    PortfolioInResponse,
    PortfolioInUpdate,
    PortfolioRiskStatusInUpdate,
    PortfolioYieldInResponse,
)
from app.schema.user import UserMessageInCreate
from app.service.datetime import get_early_morning


async def create_portfolio(
    conn: AsyncIOMotorClient, portfolio_in_db: Portfolio, reset_id: bool = True
) -> Portfolio:
    portfolio_dict = (
        portfolio_in_db.dict(by_alias=True, exclude={"id"})
        if reset_id
        else portfolio_in_db.dict(by_alias=True)
    )
    row = await get_portfolio_collection(conn).insert_one(portfolio_dict)
    portfolio_in_db.id = row.inserted_id
    return portfolio_in_db


async def delete_portfolio_by_id(
    conn: AsyncIOMotorClient, id: PyObjectId
) -> ResultInResponse:
    """根据id删除组合"""
    result = await get_portfolio_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_portfolio_by_id(
    conn: AsyncIOMotorClient, id: PyObjectId, portfolio: PortfolioInUpdate
) -> UpdateResult:
    """根据id全量更新组合，全量更新必须传入每个组合字段，无论是否更新"""
    result = await get_portfolio_collection(conn).update_one(
        {"_id": id}, {"$set": portfolio.dict()}
    )
    return UpdateResult(
        matched_count=result.matched_count, modified_count=result.modified_count
    )


async def patch_portfolio_by_id(
    conn: AsyncIOMotorClient, id: PyObjectId, portfolio_data: PortfolioInUpdate
) -> UpdateResult:
    """根据id部分更新组合，部分更新即更新某字段传入某字段，无须全部传入"""
    portfolio = await get_portfolio_collection(conn).find_one({"_id": id})
    if not portfolio:
        raise NoPortfolioError(message="需要更新的组合不存在")
    if (
        portfolio_data.config
        and "max_period" in portfolio_data.config.__fields_set__
        and not portfolio_data.close_date
    ):
        # 组合config中max_period变动，则close_date同步变动
        portfolio_data.close_date = portfolio["create_date"] + timedelta(
            days=portfolio_data.config.max_period
        )
    if portfolio_data.status == 组合状态.closed.value:
        if "activity" in portfolio.keys() and portfolio["activity"]:
            raise PortfolioCloseError(message="该组合参加了活动，不可以结束")
        # 组合关闭，同步close_date为当天
        portfolio_data.close_date = get_early_morning()
    async with await conn.start_session() as s:
        async with s.start_transaction():
            # 数据库操作放入事务中运行
            portfolio_dict = portfolio_data.dict(exclude_defaults=True)
            portfolio_dict["is_open"] = portfolio_data.is_open
            portfolio_dict["robot_config"] = portfolio_data.robot_config.dict()
            result = await get_portfolio_collection(conn).update_one(
                {"_id": id}, {"$set": portfolio_dict}
            )
            if (
                portfolio["status"] == 组合状态.running.value
                and portfolio_data.status == 组合状态.closed.value
            ):
                # 组合状态由running变更为close时，更新用户portfolio字段，向关注此组合的用户发送消息
                await get_user_collection(conn).update_one(
                    {"username": portfolio["username"]},
                    {
                        "$pull": {"portfolio.create_info.running_list": id},
                        "$addToSet": {"portfolio.create_info.closed_list": id},
                    },
                )
                subscribe_user_cursor = get_user_collection(conn).find(
                    {"portfolio": {"$in": [id]}}
                )
                message_list = [
                    UserMessageInCreate(
                        **{
                            "title": f"{portfolio['name']}",
                            "content": f"订阅的组合已被创建者关闭",
                            "category": 消息分类.portfolio,
                            "msg_type": 消息类型.subscribe,
                            "username": user["username"],
                            "data_info": f"{id}",
                        }
                    ).dict(by_alias=True)
                    async for user in subscribe_user_cursor
                ]
                if message_list:
                    await get_user_message_collection(conn).insert_many(message_list)
            return UpdateResult(
                matched_count=result.matched_count, modified_count=result.modified_count
            )


async def get_portfolio_by_id(
    conn: AsyncIOMotorClient, id: PyObjectId
) -> PortfolioInResponse:
    """根据id查询组合信息"""
    row = await get_portfolio_collection(conn).find_one({"_id": id})
    if row:
        return PortfolioInResponse(**row)


async def get_portfolio_list(
    conn: AsyncIOMotorClient, query: dict, with_paging: bool = False, **kwargs
) -> Union[List[PortfolioInResponse], PageInResponse]:
    """
    根据指定query条件，查询组合列表
    Parameters
    ----------
    conn
    query
    with_paging:  是否带有分页结构
    kwargs： 扩展信息，包含分页和排序

    Returns
    -------

    """
    db_query = {k: v for k, v in query.items() if v}
    rows = get_portfolio_collection(conn).find(db_query, **kwargs)
    if rows:
        data = [PortfolioInResponse(**row) async for row in rows]
        if not with_paging:
            return data
    else:
        data = []
    if with_paging:
        count = await get_portfolio_collection(conn).count_documents(db_query)
        return PageInResponse(
            data=data, count=count, skip=kwargs["skip"], limit=kwargs["limit"]
        )


async def get_portfolio_list_from_redis(
    query: dict, *, skip: int, limit: int
) -> List[PortfolioYieldInResponse]:
    """根据指定query条件，从redis里查询组合列表"""
    redis_key = f"{query['activity']}_portfolio_list" if query else "portfolio_list"
    portfolio_list = await G.portfolio_yield_redis.hgetall(redis_key)
    return [
        PortfolioYieldInResponse(**G.portfolio_yield_redis.hgetall(row))
        for row in portfolio_list[skip:limit]
    ]


async def get_portfolio_count(conn: AsyncIOMotorClient, db_query: dict) -> int:
    """查询指定query条件组合数量"""
    return await get_portfolio_collection(conn).count_documents(db_query)


async def bulk_write_portfolio(
    conn: AsyncIOMotorClient, operations: List[UpdateOne]
) -> None:
    """批量写入组合数据."""
    await get_portfolio_collection(conn).bulk_write(operations)


async def bulk_write_portfolio_analysis(
    conn: AsyncIOMotorClient, operations: List[UpdateOne]
) -> None:
    """批量写入组合分析数据."""
    await get_portfolio_analysis_collection(conn).bulk_write(operations)


async def update_portfolio_import_date_by_id(
    conn: AsyncIOMotorClient, portfolio_id: PyObjectId, import_date: datetime
) -> None:
    """更新组合最早导入持仓时间."""
    await get_portfolio_collection(conn).update_one(
        {"_id": portfolio_id}, {"$set": {"import_date": import_date}}
    )


async def get_portfolio_by_fund_id(
    conn: AsyncIOMotorClient, fund_id: str
) -> Optional[Portfolio]:
    row = await get_portfolio_collection(conn).find_one(
        {"fund_account.fundid": fund_id}
    )
    if row:
        return Portfolio(**row)


async def delete_portfolio_many(
    conn: AsyncIOMotorClient, dict_filter: dict
) -> ResultInResponse:
    result = await get_portfolio_collection(conn).delete_many(dict_filter)
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_risk_status(
    conn: AsyncIOMotorClient,
    portfolio: Portfolio,
    risk_list: List[PortfolioRiskStatusInUpdate],
) -> List[风险点信息]:
    """
    更新组合风险状态
    Parameters
    ----------
    conn 数据库连接
    portfolio 组合
    risk_list 待更新风险点id与状态列表
    Returns
    -------
    List[风险点信息]
    """
    risk_dict = {risk.id: risk.status for risk in risk_list}
    updated_risk_list = []
    for risk in portfolio.risks:
        if risk.id in risk_dict.keys() and risk.status != risk_dict[risk.id]:
            risk.status = risk_dict[risk.id]
            updated_risk_list.append(risk)
    portfolio.updated_at = datetime.utcnow()
    await get_portfolio_collection(conn).update_one(
        {"_id": portfolio.id}, {"$set": portfolio.dict(include={"risks", "updated_at"})}
    )
    return updated_risk_list
