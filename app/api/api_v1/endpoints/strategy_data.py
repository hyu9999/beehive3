import json
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, Body, Security, Path, Query, UploadFile, File, HTTPException
from starlette.background import BackgroundTasks
from stralib import FastTdate

from app.core.errors import ParamsError, NoEquipError
from app.core.jwt import get_current_user_authorizer
from app.crud.equipment import 查询某个装备的详情
from app.crud.strategy_data import 创建策略数据, 查询策略数据, 删除策略数据, 查询最新策略数据
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.enums.common import 回测评级数据集, 数据库排序
from app.enums.equipment import 装备信号传入方式
from app.enums.strategy_data import 策略数据类型, 策略名称, 策略名称_EN
from app.models import STRATEGY_RE
from app.schema.common import ResultInResponse
from app.schema.strategy_data import 策略数据InCreate
from app.service.airflow import AirflowTools
from app.service.strategy_data import read_strategy_data_from_file, write_strategy_data_to_adam, update_strategy_online_time

router = APIRouter()


@router.post("/{strategy_name}/{strategy_type}", description="创建策略数据", response_model=ResultInResponse)
async def create_view(
    strategy_name: 策略名称 = Path(...),
    strategy_type: 策略数据类型 = Path(...),
    strategy_data: List[dict] = Body(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:创建"]),
):
    if not strategy_data:
        raise ParamsError(message=f"创建策略数据失败，错误原因：传入列表不能为空")
    return await 创建策略数据(db, strategy_name, strategy_type, strategy_data)


@router.post("/{strategy_name}/adam/{sid}", description="根据策略id将信号写入adam", response_model=ResultInResponse)
async def create_by_sid_view(
    background_tasks: BackgroundTasks,
    strategy_name: 策略名称 = Path(...),
    sid: str = Path(..., regex=STRATEGY_RE),
    data: str = Body([], embed=True),
    file: UploadFile = File(None),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:创建"]),
):
    # 装备合法性校验
    equipment = await 查询某个装备的详情(db, sid)
    if not equipment:
        raise NoEquipError()
    if equipment.信号传入方式 != 装备信号传入方式.手动传入:
        raise ParamsError(message=f"传入参数错误，错误原因：信号传入方式错误不允许写入策略数据")
    # 数据组装
    try:
        strategy_data = [策略数据InCreate(**x) for x in json.loads(data)] if data else []
    except Exception as e:
        raise HTTPException(422, detail="传入信号格式错误")
    if file:
        data_in_file = await read_strategy_data_from_file(file)
        strategy_data.extend([策略数据InCreate(**x) for x in data_in_file])
    if not strategy_data:
        raise ParamsError(message=f"创建策略数据失败，错误原因：传入列表不能为空")

    date_list = [x.TDATE for x in strategy_data]
    start_date, end_date = min(date_list), max(date_list)
    # 写入adam
    await write_strategy_data_to_adam(sid, strategy_data, start_date, end_date)
    # 更新装备上线时间
    if equipment.上线时间 > start_date:
        col_name = f"{strategy_name if strategy_name==策略名称.机器人 else '装备'}信息collection名"
        await update_strategy_online_time(db, start_date, sid, col_name)
    # 触发airflow任务: 同步策略表
    background_tasks.add_task(AirflowTools().wait_dag_run, f"{策略名称_EN[strategy_name]}-{equipment.标识符}-2")
    return ResultInResponse()


@router.get("/{strategy_name}/{strategy_type}/{sid}", description="查询策略数据")
async def list_view(
    strategy_name: 策略名称 = Path(...),
    strategy_type: 策略数据类型 = Path(...),
    sid: str = Path(..., regex=STRATEGY_RE),
    symbol: str = Query(None, title="指数代码"),
    start: date = Query(None, title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(None, title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    数据集: 回测评级数据集 = Query(None, description="数据集，策略回测评级中使用，择时没有"),
    回测年份: str = Query(None, description="择时装备查询回测评级使用"),
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    排序: str = Query(None),
    排序方式: str = Query(None),
    push_forward: bool = Query(False, description="往前推1个交易日"),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:查询"]),
):
    filters = {"标识符": sid, "symbol": symbol}
    if 数据集:
        filters["数据集"] = 数据集
    if strategy_type == 策略数据类型.回测评级:
        if strategy_name == 策略名称.择时装备:
            if 回测年份:
                filters["回测年份"] = 回测年份
    else:
        if start and end:
            start = FastTdate.last_tdate(datetime.combine(start, datetime.min.time())) if push_forward else datetime.combine(start, datetime.min.time())
            end = datetime.combine(end, datetime.min.time())
            filters["交易日期"] = {"$gte": start, "$lte": end}
    sort = [(排序, 数据库排序[排序方式 or "正序"].value)] if 排序 else None
    return await 查询策略数据(db, strategy_name, strategy_type, filters, limit, skip, sort)


@router.delete("/{strategy_name}/{strategy_type}/{sid}", description="删除策略数据", response_model=ResultInResponse)
async def delete_view(
    strategy_name: 策略名称 = Path(...),
    strategy_type: 策略数据类型 = Path(...),
    sid: str = Path(..., regex=STRATEGY_RE),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:删除"]),
):
    return await 删除策略数据(db, strategy_name, strategy_type, filters={"标识符": sid})


@router.get("/{strategy_name}/{strategy_type}/{sid}/latest", description="查询最新策略数据")
async def latest_view(
    strategy_name: 策略名称 = Path(...),
    strategy_type: 策略数据类型 = Path(...),
    sid: str = Path(..., regex=STRATEGY_RE),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:查询"]),
):
    return await 查询最新策略数据(db, strategy_name, strategy_type, sid)
