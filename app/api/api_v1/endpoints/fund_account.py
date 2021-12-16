from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Security
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.errors import EntityDoesNotExist
from app.core.jwt import get_current_user_authorizer
from app.crud.fund_account import (
    create_fund_account_flow,
    delete_fund_account_flow_by_id,
    get_fund_account_by_id,
    get_fund_account_flow_by_id,
    update_fund_account_flow_by_id,
)
from app.crud.portfolio import get_portfolio_by_id
from app.db.mongodb import get_database
from app.enums.fund_account import FlowTType
from app.models.fund_account import FundAccountFlowInDB
from app.models.rwmodel import PyDecimal, PyObjectId
from app.schema.base import UpdateResult
from app.schema.common import ResultInResponse
from app.schema.fund_account import (
    DepositOrWithDraw,
    FundAccountFlowInCreate,
    FundAccountFlowInUpdate,
)
from app.service.fund_account.fund_account import (
    calculate_flow_fee,
    get_fund_account_flow,
    set_portfolio_import_date,
    update_fund_account_by_flow,
    update_position_by_flow,
)
from app.service.fund_account.validator import (
    capital_validation,
    date_validation,
    flow_validation,
    position_validation,
    position_validation_delete,
    pre_flow_validation,
    tdate_validation,
    time_validation,
    ttype_validation,
    user_validation,
    withdraw_validation,
)
from app.utils.datetime import date2datetime

router = APIRouter()


@router.post("/flow/", response_model=FundAccountFlowInDB, description="创建资金账户流水")
async def create_fund_account_flow_view(
    fund_account_flow: FundAccountFlowInCreate = Body(...),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    time_validation()
    ttype_validation(fund_account_flow)
    date_validation(fund_account_flow)
    pre_flow_validation(fund_account_flow)
    await flow_validation(fund_account_flow)
    try:
        fund_account = await get_fund_account_by_id(
            db, PyObjectId(fund_account_flow.fund_id)
        )
    except EntityDoesNotExist:
        raise HTTPException(400, detail=f"资金账户`{fund_account_flow.fund_id}`不存在。")
    flow = calculate_flow_fee(fund_account, fund_account_flow)
    await user_validation(db, user, flow.fund_id)
    capital_validation(fund_account, flow)
    await position_validation(db, flow)
    await update_position_by_flow(db, flow)
    flow_in_db = await create_fund_account_flow(db, flow)
    await update_fund_account_by_flow(db, fund_account, flow_in_db)
    await set_portfolio_import_date(db, fund_account)
    return flow_in_db


@router.put("/flow/{flow_id}", response_model=UpdateResult, description="更新资金账户流水")
async def update_fund_account_flow_view(
    fund_account_flow: FundAccountFlowInUpdate = Body(...),
    flow_id: PyObjectId = Path(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer()),
):
    time_validation()
    pre_flow_validation(fund_account_flow)
    # 获取该流水
    try:
        flow_in_db_raw = await get_fund_account_flow_by_id(db, flow_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail=f"未找流水`{flow_id}`。")
    # 获取资金账户
    try:
        fund_account = await get_fund_account_by_id(
            db, PyObjectId(flow_in_db_raw.fund_id)
        )
    except EntityDoesNotExist:
        raise HTTPException(400, detail=f"资金账户`{flow_in_db_raw.fund_id}`不存在。")
    # 恢复该流水对资金账户持仓和资产的影响
    flow_in_create = FundAccountFlowInCreate(**flow_in_db_raw.dict())
    flow_in_create.ttype = (
        FlowTType.SELL if flow_in_db_raw.ttype == FlowTType.BUY else FlowTType.BUY
    )
    flow = calculate_flow_fee(fund_account, flow_in_create)
    await update_position_by_flow(db, flow)
    await update_fund_account_by_flow(db, fund_account, flow)
    # 更新资金账户流水、持仓、资产
    flow_in_create = FundAccountFlowInCreate(**flow_in_db_raw.dict())
    flow_in_create.ttype = fund_account_flow.ttype
    flow_in_create.stkeffect = fund_account_flow.stkeffect
    flow_in_create.cost = fund_account_flow.cost
    flow = calculate_flow_fee(fund_account, flow_in_create)
    fund_account = await get_fund_account_by_id(db, PyObjectId(flow_in_db_raw.fund_id))
    # 如果创建时报错，则需要恢复上一步对资金账户的影响
    try:
        ttype_validation(flow_in_create)
        await flow_validation(flow_in_create)
        capital_validation(fund_account, flow)
        await position_validation(db, flow)
    except HTTPException as e:
        fund_account = await get_fund_account_by_id(
            db, PyObjectId(flow_in_db_raw.fund_id)
        )
        await update_position_by_flow(db, flow_in_db_raw)
        await update_fund_account_by_flow(db, fund_account, flow_in_db_raw)
        raise e
    await update_position_by_flow(db, flow)
    result = await update_fund_account_flow_by_id(db, flow_id, flow)
    await update_fund_account_by_flow(db, fund_account, flow)
    return result


@router.delete(
    "/flow/{flow_id}", response_model=ResultInResponse, description="删除资金账户流水"
)
async def delete_fund_account_flow_view(
    flow_id: PyObjectId = Path(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer()),
):
    time_validation()
    try:
        flow = await get_fund_account_flow_by_id(db, flow_id)
    except EntityDoesNotExist:
        raise HTTPException(400, detail=f"流水`{flow_id}`不存在。")
    ttype_validation(FundAccountFlowInCreate(**flow.dict()))
    await position_validation_delete(db, flow)
    try:
        fund_account = await get_fund_account_by_id(db, PyObjectId(flow.fund_id))
    except EntityDoesNotExist:
        raise HTTPException(400, detail=f"资金账户`{flow.fund_id}`不存在。")
    flow.fundeffect = PyDecimal(-1 * flow.fundeffect.to_decimal())
    flow.stkeffect = -flow.stkeffect
    result = await delete_fund_account_flow_by_id(db, flow_id)
    import_date = await set_portfolio_import_date(db, fund_account)
    await update_position_by_flow(db, flow)
    await update_fund_account_by_flow(db, fund_account, flow, import_date)
    return result


@router.get("/flow/", response_model=List[FundAccountFlowInDB], description="查询组合流水")
async def get_fund_account_flow_view(
    db: AsyncIOMotorClient = Depends(get_database),
    portfolio_id: PyObjectId = Query(..., description="组合ID"),
    ttype: Optional[List[FlowTType]] = Query(None, description="资金流水类别"),
    start_date: Optional[date] = Query(None, description="开始时间(格式:`2022-01-01`)"),
    end_date: Optional[date] = Query(None, description="结束时间(格式:`2022-01-01`)"),
    symbol: Optional[str] = Query(None, description="股票符号"),
    _=Security(get_current_user_authorizer()),
):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"未找组合`{portfolio_id}`。")
    results = []
    for fund_account in portfolio.fund_account:
        results.extend(
            await get_fund_account_flow(
                db,
                fund_id=fund_account.fundid,
                category=portfolio.category,
                currency=fund_account.currency,
                ttype=ttype,
                start_date=start_date,
                end_date=end_date,
                symbol=symbol,
            )
        )
    return results


@router.post("/deposit", response_model=FundAccountFlowInDB, description="入金")
async def deposit_view(
    db: AsyncIOMotorClient = Depends(get_database),
    deposit: DepositOrWithDraw = Body(...),
    _=Security(get_current_user_authorizer()),
):
    time_validation()
    date_validation(deposit)
    tdate_validation(deposit)
    try:
        fund_account = await get_fund_account_by_id(db, PyObjectId(deposit.fund_id))
    except EntityDoesNotExist:
        return HTTPException(status_code=404, detail=f"未找资金账户`{deposit.fund_id}`。")
    flow = FundAccountFlowInDB(
        fund_id=deposit.fund_id,
        ttype=FlowTType.DEPOSIT,
        tdate=date2datetime(deposit.tdate),
        currency=fund_account.currency,
        fundeffect=abs(deposit.amount.to_decimal()),
        ts=date2datetime(deposit.tdate).timestamp(),
    )
    await update_fund_account_by_flow(db, fund_account, flow)
    result = await create_fund_account_flow(db, flow)
    await set_portfolio_import_date(db, fund_account)
    return result


@router.post("/withdraw", response_model=FundAccountFlowInDB, description="出金")
async def withdraw_view(
    db: AsyncIOMotorClient = Depends(get_database),
    withdraw: DepositOrWithDraw = Body(...),
    _=Security(get_current_user_authorizer()),
):
    time_validation()
    date_validation(withdraw)
    tdate_validation(withdraw)
    try:
        fund_account = await get_fund_account_by_id(db, PyObjectId(withdraw.fund_id))
    except EntityDoesNotExist:
        return HTTPException(status_code=404, detail=f"未找资金账户`{withdraw.fund_id}`。")
    await withdraw_validation(db, withdraw, fund_account)
    flow = FundAccountFlowInDB(
        fund_id=withdraw.fund_id,
        ttype=FlowTType.WITHDRAW,
        tdate=date2datetime(withdraw.tdate),
        currency=fund_account.currency,
        fundeffect=-1 * abs(withdraw.amount.to_decimal()),
        ts=date2datetime(withdraw.tdate).timestamp(),
    )
    await update_fund_account_by_flow(db, fund_account, flow)
    result = await create_fund_account_flow(db, flow)
    await set_portfolio_import_date(db, fund_account)
    return result
