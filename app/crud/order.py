from typing import Any, List

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne

from app.crud.base import get_order_collection
from app.models.order import Order
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.order import OrderInCreate, OrderInResponse, OrderInUpdate


async def batch_create_order(
    conn: AsyncIOMotorClient, orders: List[Order]
) -> ResultInResponse:
    update_list = [InsertOne(x.dict()) for x in orders]
    if update_list:
        await get_order_collection(conn).bulk_write(update_list, ordered=False)
    return ResultInResponse()


async def create_order(conn: AsyncIOMotorClient, order: OrderInCreate) -> Order:
    order = Order(**order.dict())
    row = await get_order_collection(conn).insert_one(order.dict(exclude={"id"}))
    order.id = row.inserted_id
    return order


async def delete_order_by_id(
    conn: AsyncIOMotorClient, id: PyObjectId
) -> ResultInResponse:
    result = await get_order_collection(conn).delete_one({"_id": id})
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def delete_order_many(
    conn: AsyncIOMotorClient, dict_filter: dict
) -> ResultInResponse:
    result = await get_order_collection(conn).delete_many(dict_filter)
    if result.deleted_count > 0:
        return ResultInResponse()
    return ResultInResponse(result="failed")


async def update_order_by_id(
    conn: AsyncIOMotorClient, id: PyObjectId, order: OrderInUpdate
) -> UpdateResult:
    result = await get_order_collection(conn).update_one(
        {"_id": id}, {"$set": order.dict()}
    )
    return UpdateResult(
        matched_count=result.matched_count, modified_count=result.modified_count
    )


async def patch_order_by_id(
    conn: AsyncIOMotorClient, id: PyObjectId, order: OrderInUpdate
) -> UpdateResult:
    result = await get_order_collection(conn).update_one(
        {"_id": id}, {"$set": order.dict(exclude_defaults=True)}
    )
    return UpdateResult(
        matched_count=result.matched_count, modified_count=result.modified_count
    )


async def get_order_by_id(conn: AsyncIOMotorClient, id: PyObjectId) -> OrderInResponse:
    row = await get_order_collection(conn).find_one({"_id": id})
    if row:
        return OrderInResponse(**row)


async def get_order_by_order_id(
    conn: AsyncIOMotorClient, order_id: str
) -> OrderInResponse:
    row = await get_order_collection(conn).find_one({"order_id": order_id})
    if row:
        return OrderInResponse(**row)


async def get_orders(conn: AsyncIOMotorClient, query: dict) -> List[OrderInResponse]:
    db_query = {k: v for k, v in query.items() if v}
    rows = get_order_collection(conn).find(db_query)
    if rows:
        return [OrderInResponse(**row) async for row in rows]


async def update_order_by_bulk(
    conn: AsyncIOMotorClient, opt: List[Any], ordered: bool = False
):
    """批量更新订单"""
    await get_order_collection(conn).bulk_write(opt, ordered=ordered)
