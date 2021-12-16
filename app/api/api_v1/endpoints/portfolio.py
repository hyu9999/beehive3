from datetime import datetime, timedelta
from typing import Dict, List, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Security
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.background import BackgroundTasks
from stralib import FastTdate

from app.core.errors import ActivityAlreadyJoined, EntityDoesNotExist
from app.core.jwt import get_current_user_authorizer
from app.crud.base import format_field_sort, get_robots_collection
from app.crud.portfolio import (
    delete_portfolio_by_id,
    get_portfolio_by_id,
    get_portfolio_count,
    get_portfolio_list,
    patch_portfolio_by_id,
    update_portfolio_by_id,
    update_risk_status,
)
from app.crud.tag import 新建标签
from app.crud.user import update_user
from app.db.mongodb import get_database
from app.enums.portfolio import PortfolioCategory, ReturnYieldCalculationMethod, 组合状态
from app.enums.stock import 股票市场Enum
from app.enums.tag import TagType
from app.models.base.portfolio import 风险点信息
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import PageInResponse, ResultInResponse
from app.schema.portfolio import (
    PortfolioBasicRunDataInResponse,
    PortfolioInCreate,
    PortfolioInResponse,
    PortfolioInUpdate,
    PortfolioRiskStatusInUpdate,
)
from app.schema.user import TargetDataInResponse, UserInUpdate
from app.service.activity import join_activity
from app.service.datetime import get_early_morning
from app.service.permission import check_robot_permission
from app.service.portfolio.portfolio import (
    PortfolioTools,
    create_portfolio_service,
    get_account_asset,
    get_account_position,
    get_account_stock_position,
    get_yield_trend,
    inspect_portfolio_number_limit,
)
from app.service.portfolio.portfolio_target import PortfolioTargetTools
from app.service.portfolio.stock_statistics import StockStatisticsTools
from app.service.portfolio.trade_statistics import TradeStatisticsTools
from app.service.risks.detection import risk_detection
from app.service.risks.risk import get_all_risks
from app.service.time_series_data.time_series_data import create_init_time_series_data
from app.utils.datetime import date2tdate

router = APIRouter()


@router.post("", response_model=Portfolio, description="创建组合")
async def create_view(
    background_tasks: BackgroundTasks,
    portfolio: PortfolioInCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:创建"]),
):
    if not portfolio.activity:
        await inspect_portfolio_number_limit(db, user)
    db_query = {
        "username": user.username,
        "status": 组合状态.running.value,
        "activity": portfolio.activity,
    }
    if portfolio.activity and await get_portfolio_count(db, db_query):
        raise ActivityAlreadyJoined
    if portfolio.config.expected_return <= 0:
        raise HTTPException(400, "请输入大于0的预期收益率。")
    check_robot_permission(portfolio.robot, user)
    async with await db.start_session() as s:
        async with s.start_transaction():
            portfolio = await create_portfolio_service(db, portfolio, user)
            if not portfolio.activity:
                user.portfolio.create_info.create_num += 1
            user.portfolio.create_info.running_list.append(portfolio.id)
            await update_user(db, user.username, UserInUpdate(**user.dict()))
            if portfolio.activity:
                await join_activity(db, portfolio.activity, user.username)
    # 风险检测
    background_tasks.add_task(
        create_init_time_series_data, conn=db, portfolio=portfolio
    )
    background_tasks.add_task(risk_detection, conn=db, portfolio=portfolio)
    return portfolio


@router.get(
    "",
    response_model=Union[List[PortfolioInResponse], PageInResponse],
    description="获取组合列表",
)
async def list_view(
    activity: PyObjectId = Query(None),
    status: List[组合状态] = Query(None, description="组合状态"),
    subscriber: str = Query(None, description="订阅者"),
    username: str = Query(None, description="创建者"),
    fuzzy_query: str = Query(None, description="模糊查询"),
    field_sort: str = Query(None, description="排序"),
    limit: int = Query(0, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    db_query = {"status": {"$in": status or [组合状态.running.value]}, "activity": activity}
    if subscriber is not None and username is not None:
        db_query["$or"] = [
            {"username": username},
            {"subscribers": {"$in": [subscriber]}},
        ]
    elif username is not None:
        db_query["username"] = username
    elif subscriber is not None:
        db_query["subscribers"] = {"$in": [subscriber]}
    if fuzzy_query:
        db_query["$or"] = [
            {"name": {"$regex": f"{fuzzy_query}"}},
            {"tags": {"$regex": f"{fuzzy_query}"}},
        ]
    extra_params = {"skip": skip, "limit": limit}
    if field_sort:
        extra_params["sort"] = format_field_sort(field_sort)
    data = await get_portfolio_list(db, db_query, with_paging=True, **extra_params)
    return data


@router.get("/number", response_model=int, description="获取组合列表数量")
async def number_get_view(
    status: List[组合状态] = Query(None),
    fuzzy_query: str = Query(None, description="模糊查询"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    db_query = {"status": {"$in": status or [组合状态.running.value]}}
    if fuzzy_query:
        db_query["$or"] = [
            {"name": {"$regex": f"{fuzzy_query}"}},
            {"tags": {"$regex": f"{fuzzy_query}"}},
        ]
    return await get_portfolio_count(db, db_query)


@router.get(
    "/yield_trend/{portfolio_id}",
    response_model=Dict[
        str, Union[PortfolioInResponse, List[Dict[str, Union[float, str]]]]
    ],
    description="获取组合收益率趋势",
)
async def yield_trend_get_view(
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    push_forward: bool = Query(False),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    if push_forward:
        start_date = FastTdate.last_tdate(start_date)
    try:
        return await get_yield_trend(db, portfolio_id, start_date, end_date)
    except EntityDoesNotExist:
        raise HTTPException(404, detail=f"未找到组合`{portfolio_id}`。")


@router.get(
    "/trade_stats/{portfolio_id}", response_model=dict, description="获取组合交易统计数据"
)
async def trade_stats_get_view(
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    if not portfolio:
        raise HTTPException(404, detail=f"未找到组合`{portfolio_id}`。")
    start_date = start_date or portfolio.import_date
    end_date = end_date or get_early_morning()
    if portfolio.category == PortfolioCategory.ManualImport:
        start_date = start_date - timedelta(days=1)
        end_date = end_date - timedelta(days=1)
    start_date = date2tdate(start_date)
    end_date = date2tdate(end_date)
    ret_data = await TradeStatisticsTools.get_data(db, portfolio, start_date, end_date)
    return ret_data


@router.get(
    "/stock_stats/{portfolio_id}", response_model=list, description="获取组合个股统计数据"
)
async def stock_stats_get_view(
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    if not portfolio:
        raise HTTPException(404, detail=f"未找到组合`{portfolio_id}`。")
    start_date = start_date or portfolio.import_date
    end_date = end_date or get_early_morning()
    if portfolio.category == PortfolioCategory.ManualImport:
        start_date = start_date - timedelta(days=1)
        end_date = end_date - timedelta(days=1)
    start_date = date2tdate(start_date)
    end_date = date2tdate(end_date)
    ret_data = await StockStatisticsTools.get_data(db, portfolio, start_date, end_date)
    return ret_data


@router.get("/account_asset/{portfolio_id}", response_model=dict, description="获取账户资产")
async def asset_get_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    refresh: bool = Query(False, description="是否刷新，默认不更新"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    try:
        return await get_account_asset(db, portfolio_id, refresh)
    except EntityDoesNotExist:
        raise HTTPException(404, detail=f"未找到组合`{portfolio_id}`或该组合的资金账户。")


@router.get(
    "/account_stock_position/{portfolio_id}", response_model=dict, description="获取股票持仓"
)
async def stock_position_get_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    symbol: str = Query(..., description="股票代码"),
    exchange: 股票市场Enum = Query(..., description="交易市场代码"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    return await get_account_stock_position(db, portfolio_id, symbol)


@router.get(
    "/target_data/{portfolio_id}",
    response_model=TargetDataInResponse,
    description="获取组合指标数据",
)
async def target_data_get_view(
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    code_list: List[str] = Query(..., description="代码列表"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    return await PortfolioTargetTools.get_user_target_data(db, code_list, portfolio)


@router.get(
    "/basic_run_data/{portfolio_id}",
    response_model=PortfolioBasicRunDataInResponse,
    description="获取组合基本运行情况",
)
async def basic_run_data_get_view(
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    calculation_method: ReturnYieldCalculationMethod = Query(
        ReturnYieldCalculationMethod.SWR, description="收益率计算方式"
    ),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    try:
        return await PortfolioTools.basic_run_data(db, portfolio_id, calculation_method)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail=f"组合`{portfolio_id}`资金账户不存在。")


@router.get("/position/{portfolio_id}", response_model=dict, description="获取组合持仓信息")
async def position_get_view(
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    try:
        return await PortfolioTools.get_position(db, portfolio_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail=f"组合`{portfolio_id}`资金账户不存在。")


@router.get(
    "/position/{portfolio_id}/risk_level",
    response_model=Union[list, None],
    description="获取账户持仓股票的风险等级",
)
async def account_position_get_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    data = await get_account_position(db, portfolio)
    if data:
        # 获取股票风险等级
        robot = await get_robots_collection(db).find_one({"标识符": portfolio.robot})
        if len(robot["风控装备列表"]):
            ret_data = []
            for stock in data:
                risk_level = await PortfolioTools.get_stock_risk_level(db, robot, stock)
                ret_data.append({"symbol": stock["symbol"], "risk_level": risk_level})
            return ret_data


@router.get(
    "/risk/{portfolio_id}", response_model=List[风险点信息], description="获取总的风险信号列表"
)
async def risk_list_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    show_all: bool = Query(False, description="是否展示全部，默认不展示"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    return await get_all_risks(db, portfolio_id, show_all)


@router.put("/risk/{portfolio_id}", response_model=List[风险点信息], description="更新组合风险点状态")
async def risk_status_update_view(
    portfolio_id: PyObjectId = Path(..., description="组合id"),
    update_risk_list: List[PortfolioRiskStatusInUpdate] = Body(
        ..., description="待更新风险点列表"
    ),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:修改"]),
):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    return await update_risk_status(db, portfolio, update_risk_list)


@router.delete("/{id}", response_model=ResultInResponse, description="删除组合")
async def delete_view(
    id: PyObjectId = Path(..., description="portfolio_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:删除"]),
):
    return await delete_portfolio_by_id(db, id)


@router.put(
    "/{portfolio_id}",
    response_model=UpdateResult,
    description="全字段更新组合，缺字段将置换数据库字段为schema默认值或None",
)
async def update_view(
    background_tasks: BackgroundTasks,
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    portfolio: PortfolioInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:修改"]),
):
    db_portfolio = await get_portfolio_by_id(db, portfolio_id)
    result = await update_portfolio_by_id(db, portfolio_id, portfolio)
    if portfolio.robot and db_portfolio.robot != portfolio.robot:
        background_tasks.add_task(
            risk_detection,
            conn=db,
            portfolio=await get_portfolio_by_id(db, portfolio_id),
        )
    return result


@router.patch(
    "/{id}", response_model=UpdateResult, description="局部更新组合，仅更新传入字段，未传入字段不做更新处理"
)
async def patch_view(
    background_tasks: BackgroundTasks,
    id: PyObjectId = Path(..., description="portfolio_id"),
    portfolio: PortfolioInUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:修改"]),
):
    if portfolio.tags:
        background_tasks.add_task(
            新建标签, conn=db, tags=portfolio.tags, tag_type=TagType.组合
        )
    db_portfolio = await get_portfolio_by_id(db, id)
    result = await patch_portfolio_by_id(db, id, portfolio)
    if portfolio.robot and db_portfolio.robot != portfolio.robot:
        background_tasks.add_task(
            risk_detection, conn=db, portfolio=await get_portfolio_by_id(db, id)
        )
    return result


@router.get("/{portfolio_id}", response_model=PortfolioInResponse, description="获取组合")
async def get_view(
    portfolio_id: PyObjectId = Path(..., description="portfolio_id"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    portfolio.import_date = date2tdate(portfolio.import_date)
    return portfolio


@router.get("/position/", description="获取用户所有组合的持仓")
async def user_portfolio_position_get_view(
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:查看"]),
):
    portfolios = await get_portfolio_list(
        db, {"username": user.username, "status": 组合状态.running}
    )
    return [
        {"id": str(x.id), "name": x.name, "position": await get_account_position(db, x)}
        for x in portfolios
    ]
