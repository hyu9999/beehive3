from typing import List

from fastapi import APIRouter, Body, Depends, Security, HTTPException, Query, Path
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.jwt import get_current_user_authorizer
from app.crud.target_config import (
    create_trade_stats_conf,
    delete_trade_stats_conf_by_id,
    update_trade_stats_conf_by_id,
    patch_trade_stats_conf_by_id,
    get_trade_stats_conf_by_id,
    get_trade_stats_confs,
    create_stock_stats_conf,
    delete_stock_stats_conf_by_id,
    update_stock_stats_conf_by_id,
    patch_stock_stats_conf_by_id,
    get_stock_stats_conf_by_id,
    get_stock_stats_confs,
    create_portfolio_target_conf,
    delete_portfolio_target_conf_by_id,
    update_portfolio_target_conf_by_id,
    patch_portfolio_target_conf_by_id,
    get_portfolio_target_conf_by_id,
    get_portfolio_target_confs,
)
from app.db.mongodb import get_database
from app.models.rwmodel import PyObjectId
from app.models.target_config import TradeStatsConf, StockStatsConf, PortfolioTargetConf
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.target_config import (
    TradeStatsConfInCreate,
    TradeStatsConfInUpdate,
    TradeStatsConfInResponse,
    StockStatsConfInCreate,
    StockStatsConfInUpdate,
    StockStatsConfInResponse,
    PortfolioTargetConfInCreate,
    PortfolioTargetConfInUpdate,
    PortfolioTargetConfInResponse,
)

router = APIRouter()


@router.post("/trade_stats", response_model=TradeStatsConf, description="创建交易统计配置")
async def trade_stats_create_view(
    trade_stats_conf: TradeStatsConfInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:创建"]),
):
    try:
        return await create_trade_stats_conf(db, trade_stats_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建交易统计配置失败，错误信息: {e}")


@router.get("/trade_stats", response_model=List[TradeStatsConfInResponse], description="获取交易统计配置列表")
async def trade_stats_list_view(
    name: List[str] = Query(None),
    code: List[str] = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:查看"]),
):
    db_query = {}
    if name:
        db_query["name"] = {"$in": name}
    if code:
        db_query["code"] = {"$in": code}
    try:
        return await get_trade_stats_confs(db, db_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取交易统计配置列表失败，错误信息: {e}")


@router.delete("/trade_stats/{id}", response_model=ResultInResponse, description="删除交易统计配置")
async def trade_stats_delete_view(
    id: PyObjectId = Path(..., description="trade_stats_conf_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:删除"]),
):
    try:
        return await delete_trade_stats_conf_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除交易统计配置失败，错误信息: {e}")


@router.put("/trade_stats/{id}", response_model=UpdateResult, description="全量更新交易统计配置")
async def trade_stats_update_view(
    id: PyObjectId = Path(..., description="trade_stats_conf_id"),
    trade_stats_conf: TradeStatsConfInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:修改"]),
):
    try:
        return await update_trade_stats_conf_by_id(db, id, trade_stats_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新交易统计配置失败，错误信息: {e}")


@router.patch("/trade_stats/{id}", response_model=UpdateResult, description="部分更新交易统计配置")
async def trade_stats_patch_view(
    id: PyObjectId = Path(..., description="trade_stats_conf_id"),
    trade_stats_conf: TradeStatsConfInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:修改"]),
):
    try:
        return await patch_trade_stats_conf_by_id(db, id, trade_stats_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新交易统计配置失败，错误信息: {e}")


@router.get("/trade_stats/{id}", response_model=TradeStatsConfInResponse, description="获取交易统计配置")
async def trade_stats_get_view(
    id: PyObjectId = Path(..., description="trade_stats_conf_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:查看"]),
):
    try:
        return await get_trade_stats_conf_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取交易统计配置失败，错误信息: {e}")


@router.post("/stock_stats", response_model=StockStatsConf, description="创建个股统计配置")
async def stock_stats_create_view(
    stock_stats_conf: StockStatsConfInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:创建"]),
):
    try:
        return await create_stock_stats_conf(db, stock_stats_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建个股统计配置失败，错误信息: {e}")


@router.get("/stock_stats", response_model=List[StockStatsConfInResponse], description="获取个股统计配置列表")
async def stock_stats_list_view(
    name: List[str] = Query(None),
    code: List[str] = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:查看"]),
):
    db_query = {}
    if name:
        db_query["name"] = {"$in": name}
    if code:
        db_query["code"] = {"$in": code}
    try:
        return await get_stock_stats_confs(db, db_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取个股统计配置列表失败，错误信息: {e}")


@router.delete("/stock_stats/{id}", response_model=ResultInResponse, description="删除个股统计配置")
async def stock_stats_delete_view(
    id: PyObjectId = Path(..., description="stock_stats_conf_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:删除"]),
):
    try:
        return await delete_stock_stats_conf_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除个股统计配置失败，错误信息: {e}")


@router.put("/stock_stats/{id}", response_model=UpdateResult, description="全量更新个股统计配置")
async def stock_stats_update_view(
    id: PyObjectId = Path(..., description="stock_stats_conf_id"),
    stock_stats_conf: StockStatsConfInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:修改"]),
):
    try:
        return await update_stock_stats_conf_by_id(db, id, stock_stats_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新个股统计配置失败，错误信息: {e}")


@router.patch("/stock_stats/{id}", response_model=UpdateResult, description="部分更新个股统计配置")
async def stock_stats_patch_view(
    id: PyObjectId = Path(..., description="stock_stats_conf_id"),
    stock_stats_conf: StockStatsConfInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:修改"]),
):
    try:
        return await patch_stock_stats_conf_by_id(db, id, stock_stats_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新个股统计配置失败，错误信息: {e}")


@router.get("/stock_stats/{id}", response_model=StockStatsConfInResponse, description="获取个股统计配置")
async def stock_stats_get_view(
    id: PyObjectId = Path(..., description="stock_stats_conf_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:查看"]),
):
    try:
        return await get_stock_stats_conf_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取个股统计配置失败，错误信息: {e}")


@router.post("/portfolio_target", response_model=PortfolioTargetConf, description="创建组合指标配置")
async def portfolio_target_create_view(
    portfolio_target_conf: PortfolioTargetConfInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:创建"]),
):
    try:
        return await create_portfolio_target_conf(db, portfolio_target_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建组合指标配置失败，错误信息: {e}")


@router.get("/portfolio_target", response_model=List[PortfolioTargetConfInResponse], description="获取组合指标配置列表")
async def portfolio_target_list_view(
    name: List[str] = Query(None),
    code: List[str] = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:查看"]),
):
    db_query = {}
    if name:
        db_query["name"] = {"$in": name}
    if code:
        db_query["code"] = {"$in": code}
    try:
        return await get_portfolio_target_confs(db, db_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取组合指标配置列表失败，错误信息: {e}")


@router.delete("/portfolio_target/{id}", response_model=ResultInResponse, description="删除组合指标配置")
async def portfolio_target_delete_view(
    id: PyObjectId = Path(..., description="portfolio_target_conf_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:删除"]),
):
    try:
        return await delete_portfolio_target_conf_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除组合指标配置失败，错误信息: {e}")


@router.put("/portfolio_target/{id}", response_model=UpdateResult, description="全量更新组合指标配置")
async def portfolio_target_update_view(
    id: PyObjectId = Path(..., description="portfolio_target_conf_id"),
    portfolio_target_conf: PortfolioTargetConfInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:修改"]),
):
    try:
        return await update_portfolio_target_conf_by_id(db, id, portfolio_target_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新组合指标配置失败，错误信息: {e}")


@router.patch("/portfolio_target/{id}", response_model=UpdateResult, description="部分更新组合指标配置")
async def portfolio_target_patch_view(
    id: PyObjectId = Path(..., description="portfolio_target_conf_id"),
    portfolio_target_conf: PortfolioTargetConfInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:修改"]),
):
    try:
        return await patch_portfolio_target_conf_by_id(db, id, portfolio_target_conf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新组合指标配置失败，错误信息: {e}")


@router.get("/portfolio_target/{id}", response_model=PortfolioTargetConfInResponse, description="获取组合指标配置")
async def portfolio_target_get_view(
    id: PyObjectId = Path(..., description="portfolio_target_conf_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["指标配置:查看"]),
):
    try:
        return await get_portfolio_target_conf_by_id(db, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取组合指标配置失败，错误信息: {e}")
