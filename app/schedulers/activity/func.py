from app.crud.activity import update_activity_by_id
from app.crud.base import get_activity_collection, get_portfolio_collection
from app.db.mongodb import db
from app.enums.activity import 活动状态
from app.enums.portfolio import 组合状态
from app.schema.activity import ActivityInUpdate
from app.service.datetime import get_early_morning


async def activity_online_task():

    """
    每日活动上线

    Parameters
    ----------

    Returns
    -------

    """
    queryset = get_activity_collection(db.client).find({"status": 活动状态.pre_online.value})
    async for act in queryset:
        if act["start_time"] <= get_early_morning():
            await update_activity_by_id(db.client, act["_id"], ActivityInUpdate(status=活动状态.online.value))


async def activity_finished_task():
    """
    每日活动结算

    Parameters
    ----------

    Returns
    -------

    """

    queryset = get_activity_collection(db.client).find({"status": 活动状态.online.value, "end_time": {"$lte": get_early_morning()}})
    async for act in queryset:
        async with await db.client.start_session() as s:
            async with s.start_transaction():
                # 修改活动状态
                await update_activity_by_id(db.client, act["_id"], ActivityInUpdate(status=活动状态.offline.value))
                # 修改活动组合状态为结束
                get_portfolio_collection(db.client).update_many({"activity": act["_id"]}, {"$set": {"status": 组合状态.closed}})
