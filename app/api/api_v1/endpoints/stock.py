from collections import ChainMap
from datetime import datetime, time
from typing import Dict, List, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Security
from hq2redis import HQSourceError, SecurityNotFoundError
from hq2redis.models import SecurityHQ, SecurityInfo
from hq2redis.reader import get_security_list, get_swl2_industry_list
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from pymongo import DeleteOne, UpdateOne
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from stralib import FastTdate

from app.core.jwt import get_current_user_authorizer
from app.crud.stock import (
    bulk_write_stock_pool,
    create_favorite_stock,
    delete_favorite_stock_by_unique,
    delete_stock_pool_by_unique,
    get_favorite_stock_by_id,
    get_favorite_stock_by_unique,
    get_favorite_stocks,
    get_stock_pool_list,
    patch_favorite_stock_by_id,
    update_favorite_stock_by_id,
    查询股票列表,
)
from app.db.mongodb import get_database
from app.enums.common import 数据库操作Enum
from app.enums.security import 证券交易所
from app.enums.stock import 自选股分类
from app.models.base.stock import 股票基本信息
from app.models.rwmodel import PyObjectId
from app.models.stock import FavoriteStock
from app.outer_sys.hq import get_security_hq, get_security_info, get_security_ticks
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.stock import (
    FavoriteStockInCreate,
    FavoriteStockInResponse,
    FavoriteStockInUpdate,
    MarketIndexDataInResponse,
    StockPoolInCreate,
    股票InResponse,
    股票行情InResponse,
)
from app.service.candlestick import KDataDiagram
from app.service.stocks.stock import query_stock_price_from_jiantou

router = APIRouter()


@router.post("/favorite/", response_model=FavoriteStock, description="创建自选股")
async def create_favorite_stock_view(
    new_favorite_stock: FavoriteStockInCreate = Body(..., description="自选股票"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:创建"]),
):
    db_query = {
        "username": user.username,
        "category": new_favorite_stock.category,
        "relationship": new_favorite_stock.relationship,
    }
    # 装备和机器人必须传入标识符；组合不需要传入也不会写入标识符
    if new_favorite_stock.category in [自选股分类.equipment, 自选股分类.robot]:
        if not new_favorite_stock.sid:
            raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail="入参错误，请传入正确的标识符")
        db_query["sid"] = new_favorite_stock.sid
    else:
        new_favorite_stock.sid = None
    new_favorite_stock.username = user.username  # 用户只允许修改自己的自选股
    old_favorite_stock = await get_favorite_stock_by_unique(db, db_query)
    if not old_favorite_stock:
        return await create_favorite_stock(db, new_favorite_stock)
    new_stocks = [stock.symbol for stock in new_favorite_stock.stocks]
    for stock in old_favorite_stock.stocks:
        if stock.symbol not in new_stocks:
            new_favorite_stock.stocks.append(stock)
    await update_favorite_stock_by_id(
        db, old_favorite_stock.id, FavoriteStockInUpdate(**new_favorite_stock.dict())
    )
    return FavoriteStock(id=old_favorite_stock.id, **new_favorite_stock.dict())


@router.get(
    "/favorite/", response_model=List[FavoriteStockInResponse], description="获取自选股列表"
)
async def get_favorite_stocks_list_view(
    category: 自选股分类 = Query(None, description="自选分类"),
    sid: str = Query(None, description="标识符"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:查看"]),
):
    db_query = {"category": category, "sid": sid, "username": user.username}
    return await get_favorite_stocks(db, db_query)


@router.delete("/favorite/", response_model=UpdateResult, description="删除自选股")
async def delete_favorite_stock_view(
    category: 自选股分类 = Query(..., description="自选分类"),
    sid: str = Query(None, description="标识符"),
    symbol: List[str] = Query(..., description="symbol"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:删除"]),
):
    if category != 自选股分类.portfolio and sid is None:
        raise HTTPException(status_code=400, detail=f"缺少必填参数sid")
    return await delete_favorite_stock_by_unique(
        db,
        {"username": user.username, "category": category, "sid": sid},
        {"symbol": {"$in": symbol}},
    )


@router.put("/favorite/{id}", response_model=UpdateResult, description="更新自选股全部字段")
async def update_favorite_stock_view(
    id: PyObjectId = Path(..., description="favorite_stock_id"),
    favorite_stock: FavoriteStockInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:修改"]),
):
    try:
        return await update_favorite_stock_by_id(db, id, favorite_stock)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新自选股失败，错误信息: {e}")


@router.patch("/favorite/{id}", response_model=UpdateResult, description="更新自选股指定字段")
async def patch_favorite_stock_view(
    id: PyObjectId = Path(..., description="favorite_stock_id"),
    favorite_stock: FavoriteStockInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:修改"]),
):
    try:
        return await patch_favorite_stock_by_id(db, id, favorite_stock)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新自选股失败，错误信息: {e}")


@router.get(
    "/favorite/{id}", response_model=FavoriteStockInResponse, description="获取自选股"
)
async def get_favorite_stock_view(
    id: PyObjectId = Path(..., description="favorite_stock_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:查看"]),
):
    try:
        return await get_favorite_stock_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取自选股失败，错误信息: {e}")


@router.get(
    "/market_index_data",
    response_model=List[MarketIndexDataInResponse],
    description="获取市场指数数据",
)
async def get_market_index_data(
    symbol: str = Query(..., regex="^[0-9]{6}$", description="股票代码，必须是6位0-9数字组成"),
    start_date: datetime = Query(
        ..., title="开始日期", description="ISO 8601日期格式的字符串, 如: 2020-01-01 00:00:00"
    ),
    end_date: datetime = Query(
        ..., title="结束日期", description="ISO 8601日期格式的字符串, 如: 2020-01-01 00:00:00"
    ),
    push_forward: bool = Query(False),
):
    if push_forward:
        start_date = FastTdate.last_tdate(start_date)
    try:
        return [
            MarketIndexDataInResponse(**x)
            for x in KDataDiagram(symbol=symbol).market(
                start_date.date(), end_date.date()
            )
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取市场指数数据失败，错误信息: {e}")


@router.post(
    "/quotation", response_model=List[SecurityHQ], description="根据传入股票信息返回相应的行情数据"
)
async def quotation_list_view(
    symbol_exchange_list: List[str] = Body(
        ..., embed=True, description="股票市场字符串列表，如[000001_0,600001_1]"
    )
):
    results = []
    for code in symbol_exchange_list:
        symbol, exchange = code.split("_")
        try:
            security = await get_security_hq(symbol, exchange)
        except (ValidationError, HQSourceError, SecurityNotFoundError):
            continue
        else:
            results.append(security)
    return results


@router.get("/info", response_model=List[SecurityInfo], description="获取全部股票基本信息")
async def stock_info_list_view(
    symbol_exchange_list: List[str] = Body(None, description="股票列表"),
):
    results = []
    symbol_exchange_list = (
        symbol_exchange_list if symbol_exchange_list else await get_security_list()
    )
    for code in symbol_exchange_list:
        symbol, exchange = code.split(".")
        exchange = "1" if exchange == "SH" else "0"
        try:
            security = await get_security_info(symbol, exchange)
        except (ValidationError, HQSourceError):
            continue
        else:
            results.append(security)
    return results


@router.get("/k_line", response_model=List[dict], description="股票k线图")
async def get_stock_k_line_view(
    symbol: str = Query(..., regex="^[0-9]{6}$", description="股票代码，必须是6为0-9数字组成"),
    exchange: 证券交易所 = Query(..., description="交易所"),
    start_date: datetime = Query(
        ..., title="开始日期", description="ISO 8601日期格式的字符串, 如: 2020-01-01 00:00:00"
    ),
    end_date: datetime = Query(
        ..., title="结束日期", description="ISO 8601日期格式的字符串, 如: 2020-01-01 00:00:00"
    ),
):
    data = KDataDiagram(symbol=symbol, exchange=exchange).stock(start_date, end_date)
    return data


@router.get(
    "/five_real_time_price",
    response_model=Dict[str, Union[str, float, int, time, 证券交易所]],
    description="获取五档图",
)
async def get_stock_k_line_view(
    symbol: str = Query(..., regex="^[0-9]{6}$", description="股票代码，必须是6为0-9数字组成"),
    exchange: 证券交易所 = Query(..., description="交易所"),
):
    try:
        raw_data = await get_security_ticks(symbol, exchange)
        data = {
            "bjw1": raw_data.bid1_p,
            "bsl1": raw_data.bid1_v,
            "bjw2": raw_data.bid2_p,
            "bsl2": raw_data.bid2_v,
            "bjw3": raw_data.bid3_p,
            "bsl3": raw_data.bid3_v,
            "bjw4": raw_data.bid4_p,
            "bsl4": raw_data.bid4_v,
            "bjw5": raw_data.bid5_p,
            "bsl5": raw_data.bid5_v,
            "sjw1": raw_data.ask1_p,
            "ssl1": raw_data.ask1_v,
            "sjw2": raw_data.ask2_p,
            "ssl2": raw_data.ask2_v,
            "sjw3": raw_data.ask3_p,
            "ssl3": raw_data.ask3_v,
            "sjw4": raw_data.ask4_p,
            "ssl4": raw_data.ask4_v,
            "sjw5": raw_data.ask5_p,
            "ssl5": raw_data.ask5_v,
        }
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"获取五档图失败，错误信息: {e}")


@router.get("/swl2_industry_list/", description="获取申万二级行业列表")
async def get_swl2_industry_list_view():
    return [industry_info.name for industry_info in await get_swl2_industry_list()]


@router.get("/stock_pool/", response_model=List[dict], description="查询组合股票池")
async def stock_info_list_view(
    portfolio_id: PyObjectId = Query(..., description="组合id"),
    group: str = Query(None, description="分组"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:查看"]),
):
    query = {"portfolio_id": portfolio_id, "group": group}
    return await get_stock_pool_list(db, query=query)


@router.delete("/stock_pool/", response_model=ResultInResponse, description="删除组合股票池")
async def stock_info_list_view(
    portfolio_id: PyObjectId = Query(..., description="组合id"),
    group: str = Query(None, description="分组"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:查看"]),
):
    query = {"portfolio_id": portfolio_id, "group": group}
    return await delete_stock_pool_by_unique(db, query=query, many=True)


@router.post("/stock_pool/", response_model=ResultInResponse, description="股票池-自选股操作")
async def favorite_batch_update_view(
    operator: 数据库操作Enum = Body(None, embed=True),
    stock_list: List[StockPoolInCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["自选股:修改"]),
):
    data_list = []
    for stock in stock_list:
        stock_dict = stock.dict()
        operator = stock_dict.pop("operator", None) or operator
        if operator in [数据库操作Enum.CREATE, 数据库操作Enum.UPDATE]:
            data_list.append(
                UpdateOne(
                    {
                        "portfolio_id": stock.portfolio_id,
                        "group": stock.group,
                        "symbol": stock.symbol,
                    },
                    {"$set": stock_dict},
                    upsert=True,
                )
            )
        elif operator == 数据库操作Enum.DELETE:
            data_list.append(DeleteOne(stock_dict))
    await bulk_write_stock_pool(db, data_list)
    return ResultInResponse()


# 建投接口
@router.get("/list", response_model=List[股票InResponse])
async def query_stock_list(
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    return await 查询股票列表(db, limit=limit, skip=skip)


@router.post("/hq", response_model=List[股票行情InResponse])
async def query_stock_hq(
    stocks: List[股票基本信息] = Body(..., embed=True),
    user=Security(get_current_user_authorizer()),
):
    """获取所有股票信息"""
    stock_list = [f"{x.symbol}_{x.exchange}" for x in stocks]
    queryset = await query_stock_price_from_jiantou(stock_list)
    data = [股票行情InResponse(**x) for x in queryset]
    return data
