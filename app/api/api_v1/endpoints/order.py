from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Security
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.background import BackgroundTasks

from app.core.errors import CancelOrderError, OrderAuthError
from app.core.jwt import get_current_user_authorizer
from app.crud.base import get_order_collection
from app.crud.order import (
    create_order,
    delete_order_by_id,
    get_order_by_id,
    get_orders,
    patch_order_by_id,
    update_order_by_id,
)
from app.crud.portfolio import get_portfolio_by_id
from app.db.mongodb import get_database
from app.enums.log import 买卖方向
from app.enums.order import 订单状态
from app.global_var import G
from app.models.base.order import 股票订单基本信息
from app.models.order import Order
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.order import (
    CreateEntrustOrderInResponse,
    DeleteEntrustOrderInResponse,
    EntrustOrderInResponse,
    OrderInCreate,
    OrderInResponse,
    OrderInUpdate,
    TaskOrderInResponse,
)
from app.service.orders.entrust_order import (
    get_entrust_orders,
    get_recent_entrust_orders,
)
from app.service.orders.order import update_task_status
from app.service.orders.order_trade_put import entrust_orders

router = APIRouter()


@router.post("", response_model=Order, description="创建订单")
async def create_order_view(
    order: OrderInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:创建"]),
):
    try:
        return await create_order(db, order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建订单失败，错误信息: {e}")


@router.delete("/{order_id}", response_model=ResultInResponse, description="删除订单")
async def delete_order_view(
    db: AsyncIOMotorClient = Depends(get_database),
    order_id: str = Path(..., description="order_id"),
    user=Security(get_current_user_authorizer(), scopes=["组合:删除"]),
):
    return await delete_order_by_id(db, PyObjectId(order_id))


@router.put("/{id}", response_model=UpdateResult, description="全量更新订单")
async def update_order_view(
    id: str = Path(..., description="order_id"),
    order: OrderInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:修改"]),
):
    try:
        return await update_order_by_id(db, PyObjectId(id), order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新订单失败，错误信息: {e}")


@router.patch("/{id}", response_model=UpdateResult, description="部分更新订单")
async def patch_order_view(
    id: str = Path(..., description="order_id"),
    order: OrderInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:修改"]),
):
    try:
        return await patch_order_by_id(db, PyObjectId(id), order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新订单失败，错误信息: {e}")


@router.get("/list", response_model=List[OrderInResponse], description="获取订单列表")
async def get_orders_view(
    portfolio: str = Query(None, description="组合ID，多个ID用','连接"),
    fund_id: str = Query(None, description="资金账户ID，多个ID用','连接"),
    status: 订单状态 = Query(None, description="订单状态"),
    operator: 买卖方向 = Query(None, description="买卖方向(buy/sell)"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    db_query = {"status": status, "operator": operator}
    if portfolio:
        db_query["portfolio"] = {"$in": [PyObjectId(p) for p in portfolio.split(",")]}
    if fund_id:
        db_query["fund_id"] = {"$in": fund_id.split(",")}
    try:
        return await get_orders(db, db_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取订单列表失败，错误信息: {e}")


@router.get("/{id}", response_model=OrderInResponse, description="获取订单")
async def get_order_view(
    id: str = Path(..., description="order_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    try:
        return await get_order_by_id(db, PyObjectId(id))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取订单失败，错误信息: {e}")


@router.post(
    "/{portfolio_id}/entrust_orders",
    response_model=CreateEntrustOrderInResponse,
    description="委托下单",
)
async def entrust_order_create_view(
    portfolio_id: PyObjectId = Path(..., description="组合ID"),
    orders: List[股票订单基本信息] = Body(..., embed=True, description="委托订单列表"),
    is_task: bool = Body(False, embed=True, description="是否是解决方案建议的委托"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:创建"]),
):
    """
    委托下单, 交易时间内直接下单, 交易时间外系统会在下一个交易日下单
    """
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    return await entrust_orders(db, user, portfolio, orders, is_task=is_task)


@router.get(
    "/{portfolio_id}/entrust_orders",
    response_model=List[EntrustOrderInResponse],
    description="查询委托记录",
)
async def entrust_order_list_view(
    portfolio_id: str = Path(..., description="组合ID"),
    op_flag: int = Query(..., description="委托订单类型"),
    start_date: str = Query(None, description="开始时间"),
    stop_date: str = Query(None, description="结束时间"),
    is_recent: bool = Query(False, description="是否查询最近的委托单记录"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    """
    委托订单历史记录查询
    Parameters
    ----------
    is_recent: 若查询最近的委托记录，则先判断当日有无委托记录，则查询上一次交易
    op_flag: 1=委托 2=成交 3=可撤
    user, db, start_date, stop_date, portfolio_id
    """
    if op_flag not in [1, 2, 3]:
        raise HTTPException(400, detail="请输入正确的op_flag参数，1=委托 2=成交 3=可撤")
    portfolio = await get_portfolio_by_id(db, PyObjectId(portfolio_id))
    if is_recent:
        return await get_recent_entrust_orders(db, portfolio, op_flag)
    return await get_entrust_orders(portfolio, start_date, stop_date, op_flag)


@router.delete(
    "/{portfolio_id}/entrust_orders/{order_id}",
    response_model=DeleteEntrustOrderInResponse,
    description="取消委托下单",
)
async def entrust_order_delete_view(
    background_tasks: BackgroundTasks,
    portfolio_id: str = Path(..., description="组合ID"),
    order_id: Optional[str] = Path(None, description="委托订单ID"),
    db_id: Optional[str] = Query(None, description="数据库订单ID"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:修改"]),
):
    """
    取消委托订单
    """
    portfolio = await get_portfolio_by_id(db, PyObjectId(portfolio_id))
    if not user.username == portfolio.username:
        raise OrderAuthError
    data = None
    if db_id:
        order = await get_order_by_id(db, PyObjectId(db_id))
        if not order:
            raise HTTPException(404, "未找到该订单。")
        order_in_update = OrderInUpdate(**order.dict())
        order_in_update.status = 订单状态.canceled
        await update_order_by_id(db, PyObjectId(db_id), order_in_update)
        if order.task:
            background_tasks.add_task(update_task_status, db, order.task, portfolio)
    else:
        tir = await G.trade_system.order_cancel(
            portfolio.fund_account[0].fundid, order_id
        )
        if not tir.flag:
            raise CancelOrderError(message=tir.msg)
        data = tir.data
    return DeleteEntrustOrderInResponse(
        status=True,
        explain="取消委托订单成功",
        data={"order_id": order_id, "order_status": data},
    )


@router.get(
    "/task_orders/{task_id}", response_model=TaskOrderInResponse, description="查询任务订单详情"
)
async def task_order_get_view(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    """查询任务订单详情"""
    orders = await get_orders(db, {"task": task_id})
    if orders:
        ret_data = {
            "id": str(task_id) if task_id else "",
            "create_date": orders[0].create_datetime,
            "orders": orders,
        }
        return TaskOrderInResponse(**ret_data)
    else:
        raise HTTPException(404, "未找到该任务订单")


@router.get(
    "/task_orders/", response_model=List[TaskOrderInResponse], description="查询任务订单"
)
async def task_order_list_view(
    order_id: str = Query(None, description="委托订单ID"),
    portfolio_id: PyObjectId = Query(None, description="组合ID"),
    category: str = Query("current", description="查询类型"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    """
    查询任务订单
    Parameters
    ----------
    category: current / history / all
    order_id, portfolio_id, db, user
    """
    query_dict = {
        "username": user.username,
    }
    if portfolio_id is not None:
        query_dict["portfolio"] = portfolio_id
    if order_id is not None:
        query_dict["order_id"] = order_id
    if category == "current":
        query_dict["status"] = {"$in": [订单状态.waiting.value, 订单状态.in_progress.value]}
    elif category == "history":
        query_dict["status"] = {
            "$in": [
                订单状态.all_finished.value,
                订单状态.failed.value,
                订单状态.order_failed.value,
                订单状态.canceled.value,
            ]
        }
    orders = await get_orders(db, query_dict)
    if category == "current":
        orders = [order for order in orders if order.task]
    results = defaultdict(list)
    for order in orders:
        results[order.task].append(order)
    return [
        TaskOrderInResponse(**dict(id=k, create_date=v[0].create_datetime, orders=v))
        for k, v in results.items()
    ]
