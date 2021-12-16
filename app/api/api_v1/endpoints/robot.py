import math
from datetime import date, datetime
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body, Security
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from starlette.background import BackgroundTasks
from starlette.responses import UJSONResponse, StreamingResponse
from starlette.status import HTTP_400_BAD_REQUEST
from stralib import FastTdate

from app import settings
from app.core.errors import RobotAlreadyExist, ClientPermissionDenied
from app.core.jwt import get_current_user_authorizer
from app.crud.base import get_equipment_collection, get_robots_collection
from app.crud.client_base import get_client_robot_count
from app.crud.file import download_stream
from app.crud.robot import (
    查询某机器人信息,
    获取机器人评价数据,
    查询机器人列表,
    创建机器人,
    删除某机器人,
    修改机器人,
    获取机器人回测指标数据,
    获取机器人回测信号数据,
    获取机器人回测评级数据,
    获取机器人实盘信号数据,
    获取机器人实盘指标数据,
    查询我的机器人列表,
    获取最新机器人实盘指标数据,
    获取最新机器人实盘信号数据,
    获取机器人回测详情数据,
    创建机器人实盘回测数据,
    更新机器人状态,
    修改机器人的运行数据,
    查询是否有该机器人,
    优选推荐机器人,
    推荐列表,
    get_robot_user_list,
)
from app.crud.tag import 新建标签
from app.crud.user import get_user_by_nickname
from app.crud_permissions.robot import 是否有修改机器人权限, 是否有删除机器人权限
from app.db.mongodb import get_database
from app.enums.common import 回测评级数据集, 数据库排序
from app.enums.robot import 机器人状态, 机器人评级
from app.enums.tag import TagType
from app.models.robot import 机器人回测指标, 机器人回测信号, 机器人回测评级, 机器人实盘信号, 机器人实盘指标, Robot
from app.outer_sys.stralib.robot.run_robot import update_stralib_robot_data
from app.schema.common import ResultInResponse
from app.schema.robot import (
    机器人inResponse,
    机器人inCreate,
    机器人InUpdate,
    机器人详情InResponse,
    机器人回测详情InResponse,
    机器人回测指标InCreate,
    机器人回测信号InCreate,
    机器人回测评级InCreate,
    机器人实盘信号InCreate,
    机器人实盘指标InCreate,
    机器人商城列表InResponse,
    机器人推荐InResponse,
    机器人推荐列表InResponse,
    智道机器人列表InResponse,
    机器人状态InUpdate,
)
from app.service.airflow import AirflowTools
from app.service.datetime import get_early_morning
from app.service.permission import check_robot_permission
from app.service.robots.robot import 生成机器人标识符, 机器人数量限制

router = APIRouter()


@router.get("/{sid}", description="获取某机器人信息", response_model=Union[机器人详情InResponse, 机器人inResponse])
async def get_a_robot_information(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    show_detail=Query(None, description="展示装备详情"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    check_robot_permission(sid, user)
    return await 查询某机器人信息(db, sid, show_detail=show_detail, user=user)


@router.get("", response_model=Union[List[机器人inResponse], 智道机器人列表InResponse], description="根据查询的条件返回满足条件的机器人列表信息")
async def query_robot_list(
    名称: str = Query(None),
    标识符: str = Query(None, max_length=14, min_length=14),
    作者: str = Query(None, max_length=14, min_length=3),
    状态: List[机器人状态] = Query(None),
    上线时间: List[datetime] = Query(None),
    下线时间: List[datetime] = Query(None),
    标签: List[str] = Query(None),
    排序: str = Query(None),
    模糊查询: List[str] = Query(None),
    search_name: str = Query(None),
    limit: int = Query(20, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    is_paging: bool = Query(False),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    """
    查询机器人列表，可按照以下参数查询 TODO 使用搜索功能实现
    """
    query = {"名称": 名称, "标识符": 标识符, "作者": 作者, "标签": 标签}
    if 状态:
        query["状态"] = {"$in": 状态}
    if 上线时间:
        query["上线时间"] = {"$gte": min(上线时间), "$lte": max(上线时间)}
    if 下线时间:
        query["下线时间"] = {"$gte": min(下线时间), "$lte": max(下线时间)}
    if search_name and 模糊查询:
        query["$or"] = [{x: {"$regex": f"{search_name}"}} for x in 模糊查询]
    order_by_list = [(x.split("=")[0], int(x.split("=")[1])) for x in 排序.split(",")] if 排序 else [("上线时间", -1)]
    robot_list = await 查询机器人列表(db, query, limit, skip, order_by=order_by_list, user=user)
    if not is_paging:
        return robot_list
    documents_count = await get_client_robot_count(db, query, user)
    page_size = math.ceil(documents_count / limit) if limit > 0 else 1
    return 智道机器人列表InResponse(数据=robot_list, 总数据量=documents_count, 总页数=page_size)


@router.get("/zhidao/user", response_model=智道机器人列表InResponse, description="查询智道用户的机器人列表信息")
async def query_robot_list(
    limit: int = Query(0, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    标签: List[str] = Query(None),
    排序: str = Query("管理了多少组合"),
    排序方式: str = Query("倒序"),
    模糊查询: List[str] = Query(None),
    search_name: str = Query(None),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    if 排序 not in ["创建时间", "管理了多少组合", "累计管理资金", "累计产生信号数"]:
        raise HTTPException(422, detail="错误的排序类型")
    db_query = {
        "状态": "已上线",
        "$or": [
            {"评级": {"$ne": "N"}, "作者": user.username},
            {"评级": {"$in": ["A", "B", "C"]}, "作者": {"$ne": user.username}, "可见模式": "完全公开"},
        ],
    }
    if 标签:
        db_query["标签"] = {"$all": 标签}  # 标签取交集
    if search_name:
        if 模糊查询:
            db_query.update({"$or": [{x: {"$regex": f"{search_name}"}} for x in 模糊查询]})
        else:
            db_query.update({"$or": [{"名称": search_name}, {"标签": {"$in": [search_name]}}]})
    robots_list = await 查询机器人列表(db, db_query, limit, skip, [(排序, 数据库排序[排序方式].value)], user)
    documents_count = await get_client_robot_count(db, db_query, user)
    page_size = math.ceil(documents_count / limit) if limit > 0 else 1
    return 智道机器人列表InResponse(数据=robots_list, 总数据量=documents_count, 总页数=page_size)


@router.get("/my/list", response_model=List[Robot], description="查询我的机器人信息列表，根据装备查询的条件返回装备信息")
async def query_my_robot_list(
    筛选: str = Query(None),
    排序: str = Query("创建时间"),
    排序方式: str = Query("倒序"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    if 排序 not in ["创建时间", "管理了多少组合", "累计管理资金", "累计产生信号数"]:
        raise HTTPException(422, detail="错误的排序类型")
    return await 查询我的机器人列表(db, 筛选, 排序, 排序方式, user)


@router.get("/store/list", response_model=机器人商城列表InResponse, description="查询商城内的机器人列表")
async def query_store_robot_list(
    search: str = Query(None, description="全文搜索内容"),
    昵称: List[str] = Query(None),
    标签: List[str] = Query(None),
    排序: str = Query("累计收益率"),
    排序方式: str = Query("倒序"),
    limit: int = Query(20, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    if 排序 not in ["分析了多少支股票", "累计创造收益", "运行天数", "累计产生信号数", "累计服务人数", "上线时间", "订阅人数", "累计收益率"]:
        raise HTTPException(422, detail="错误的排序类型")
    筛选 = {"状态": "已上线", "可见模式": "完全公开", "评级": {"$in": ["A", "B", "C"]}}
    if search:
        筛选["$or"] = [{"名称": {"$regex": f"{search}"}}, {"标识符": {"$regex": f"{search}"}}, {"作者": {"$regex": f"{search}"}}]
    if 标签:
        筛选["标签"] = {"$in": 标签}
    if 昵称:
        auths = await get_user_by_nickname(db, 昵称)
        筛选["作者"] = {"$in": [auth.username for auth in auths]}
    robots_list = await 查询机器人列表(db, 筛选, limit, skip, [(排序, 数据库排序[排序方式].value)], user)
    documents_count = await get_client_robot_count(db, 筛选, user)
    page_size = math.ceil(documents_count / limit) if limit > 0 else 1
    return 机器人商城列表InResponse(数据=robots_list, 总数据量=documents_count, 总页数=page_size)


@router.get("/check_exist/", description="查询某机器人是否存在", response_model=ResultInResponse)
async def check_robot_exist(
    name: str = Query(None),
    sid: str = Query(None, regex=r"^(10|15)[\d]{6}[\w]{4}[\d]{2}$", min_length=14, max_length=14),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:创建"]),
):
    result = await 查询是否有该机器人(db, {"$or": [{"名称": name, "状态": {"$nin": ["已删除", "临时回测"]}}, {"标识符": sid}]})
    return ResultInResponse(result=result)


@router.post("/new", description="新建机器人", response_model=机器人inResponse)
async def create_new_robot(
    background_tasks: BackgroundTasks,
    实时审核: bool = Query(True, description="是否需要实时审核"),
    机器人: 机器人inCreate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:创建"]),
):
    if settings.manufacturer_switch:
        raise ClientPermissionDenied()
    await 机器人数量限制(user, db)
    is_exist = await 查询是否有该机器人(db, {"$or": [{"名称": 机器人.名称, "状态": {"$nin": ["已删除", "临时回测"]}}, {"标识符": 机器人.标识符}]})
    if is_exist == "success":
        raise RobotAlreadyExist
    机器人字典 = 机器人.dict()
    机器人字典["作者"] = user.username
    packages_cursor = get_equipment_collection(db).find({"标识符": {"$in": 机器人字典["风控包列表"]}})
    机器人字典["风控装备列表"] = list({sid async for row in packages_cursor if row for sid in row["装备列表"]})
    current_dt = datetime.utcnow()
    机器人字典["创建时间"] = current_dt
    if len(机器人.选股装备列表) > 0 and len(机器人.择时装备列表) > 0 and len(机器人.交易装备列表) > 0:
        start_index = 10
        机器人字典["状态"] = 机器人状态.审核中
    else:
        start_index = 15
        机器人字典["状态"] = 机器人状态.已上线
        机器人字典["上线时间"] = current_dt
    机器人字典["标识符"] = 机器人.标识符 or await 生成机器人标识符(db, start_index)
    if not 机器人字典["标识符"].startswith(str(start_index)):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建机器人失败，标识符不符合规则，应以'{start_index}'开头！")
    try:
        await 新建标签(db, 机器人.标签, TagType.机器人)
        robot = await 创建机器人(db, Robot(**机器人字典))
        if 实时审核 and robot.标识符.startswith("10"):
            background_tasks.add_task(AirflowTools().wait_dag_run, f"robot-{robot.标识符}-2")
        return robot
    except DuplicateKeyError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建机器人失败，{e.details.get('keyValue')}已存在")


@router.put("/{sid}", description="更新机器人", response_model=ResultInResponse)
async def update_a_robot(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    机器人: 机器人InUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:修改", "机器人:修改他人"]),
):
    check_robot_permission(sid, user)
    await 是否有修改机器人权限(sid, user, db)
    return await 修改机器人(db, sid, 机器人)


@router.put("/{sid}/operational", description="更新机器人的运行数据", response_model=ResultInResponse)
async def robot_operational_update_view(
    background_tasks: BackgroundTasks,
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:修改", "机器人:修改他人"]),
):
    await 是否有修改机器人权限(sid, user, db)
    result = await 修改机器人的运行数据(db, sid)
    background_tasks.add_task(update_stralib_robot_data, sid=sid, tdate=get_early_morning())
    return result


@router.delete("/{sid}", description="删除某机器人", response_model=int, response_description="返回删除的条数")
async def remove_a_robot(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:删除", "机器人:删除他人"]),
):
    await 是否有删除机器人权限(sid, user, db)
    return await 删除某机器人(db, sid)


@router.get("/{sid}/assess_result", description="查询机器人评估评级信息", response_class=UJSONResponse)
async def query_robot_assess_result(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    end: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15."),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看", "稻草人数据:查看他人"]),
):
    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    result = await 获取机器人评价数据(sid, start, end)
    return result.to_json(orient="records", index=True)


@router.get("/logo/{sid}", description="获取机器人头像。", response_description="直接返回content-type指定的文件")
async def get_robot_logo(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    user: Optional = Security(get_current_user_authorizer(required=False), scopes=["机器人:查看他人", "机器人:查看"]),
    db: AsyncIOMotorClient = Depends(get_database),
):
    file = await download_stream(db, sid)
    return StreamingResponse(file.__iter__(), media_type=file.content_type)


@router.get("/{sid}/backtest_indicator", description="查询机器人回测指标数据", response_model=List[机器人回测指标])
async def get_robot_backtest_indicator(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15."),
    limit: int = Query(20, gt=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    return await 获取机器人回测指标数据(db, sid, start, end, limit, skip)


@router.get("/{sid}/backtest_signal", description="查询机器人回测信号", response_model=List[机器人回测信号])
async def get_robot_backtest_signal(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    end: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15."),
    limit: int = Query(20, gt=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    return await 获取机器人回测信号数据(db, sid, start, end, limit, skip)


@router.get("/{sid}/backtest_assess", description="查询机器人回测评级", response_model=List[机器人回测评级])
async def get_robot_backtest_assess(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    return await 获取机器人回测评级数据(db, sid)


@router.get("/{sid}/real_signal", description="查询机器人实盘信号", response_model=List[机器人实盘信号])
async def get_robot_real_signal(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    end: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15."),
    limit: int = Query(20, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    排序方式: str = Query("倒序", description="排序方式默认倒序"),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    check_robot_permission(sid, user)
    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    return await 获取机器人实盘信号数据(db, sid, start, end, limit, skip, 排序方式)


@router.get("/{sid}/real_signal/latest", description="查询机器人最新实盘信号数据", response_model=List[机器人实盘信号])
async def get_latest_robot_real_signal(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    return await 获取最新机器人实盘信号数据(db, sid)


@router.get("/{sid}/real_indicator", description="查询机器人实盘指标数据", response_model=List[机器人实盘指标])
async def get_robot_real_indicator(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15."),
    push_forward: bool = Query(False, description="往前推1个交易日"),
    limit: int = Query(20, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    排序: str = Query("交易日期"),
    排序方式: str = Query("正序"),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    check_robot_permission(sid, user)
    start = datetime.combine(start, datetime.min.time())
    if push_forward:
        start = FastTdate.last_tdate(start)
    end = datetime.combine(end, datetime.min.time())
    return await 获取机器人实盘指标数据(db, sid, start, end, limit, skip, [(排序, 数据库排序[排序方式].value)])


@router.get("/{sid}/real_indicator/latest", description="查询机器人最新实盘指标数据", response_model=机器人实盘指标)
async def get_latest_robot_real_indicator(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    return await 获取最新机器人实盘指标数据(db, sid)


@router.get("/backtest/details/{sid}", description="查询机器人回测详情", response_model=机器人回测详情InResponse)
async def get_robot_backtest_details(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    数据集: 回测评级数据集 = Query("测试集评级", description="数据集"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    return await 获取机器人回测详情数据(db, sid, 数据集)


@router.post("/backtest_indicator", description="创建机器人回测指标数据", response_model=ResultInResponse)
async def create_robot_backtest_indicator(
    机器人回测指标数据: List[机器人回测指标InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    return await 创建机器人实盘回测数据(db, "机器人回测指标collection名", 机器人回测指标数据)


@router.post("/backtest_signal", description="创建机器人回测信号数据", response_model=ResultInResponse)
async def create_robot_backtest_signal(
    机器人回测信号数据: List[机器人回测信号InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    return await 创建机器人实盘回测数据(db, "机器人回测信号collection名", 机器人回测信号数据)


@router.post("/backtest_assess", description="创建机器人回测评级数据", response_model=ResultInResponse)
async def create_robot_backtest_assess(
    机器人回测评级数据: List[机器人回测评级InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    return await 创建机器人实盘回测数据(db, "机器人回测评级collection名", 机器人回测评级数据)


@router.post("/real_signal", description="创建机器人实盘信号数据", response_model=ResultInResponse)
async def create_robot_real_signal(
    机器人实盘信号数据: List[机器人实盘信号InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    return await 创建机器人实盘回测数据(db, "机器人实盘信号collection名", 机器人实盘信号数据)


@router.post("/real_indicator", description="创建机器人实盘指标数据", response_model=ResultInResponse)
async def create_robot_real_indicator(
    机器人实盘指标数据: List[机器人实盘指标InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    return await 创建机器人实盘回测数据(db, "机器人实盘指标collection名", 机器人实盘指标数据)


@router.put("/{sid}/action", description="更新某机器人状态")
async def update_robot_status(
    robot_state_in_update: 机器人状态InUpdate = Body(...),
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:修改", "机器人:修改他人"]),
):
    await 是否有修改机器人权限(sid, user, db)
    return await 更新机器人状态(db, sid, robot_state_in_update)


@router.put("/{sid}/offline_reason", description="更新某装备的下线原因")
async def update_offline_reason(
    sid: str = Path(..., regex="^(10|15)", min_length=14, max_length=14),
    下线原因: str = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:修改", "装备:修改他人"]),
):
    check_robot_permission(sid, user)
    await 是否有修改机器人权限(sid, user, db)
    机器人 = await 查询某机器人信息(db, sid, show_detail=False, user=user)
    if 机器人.状态 != "已下线":
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"该状态不允许修改下线原因")
    await get_robots_collection(db).update_one({"标识符": sid}, {"$set": {"下线原因": 下线原因}})
    return ResultInResponse()


@router.get("/recommend/", response_model=List[机器人推荐InResponse], description="优选推荐机器人")
async def recommend_robots(
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    return await 优选推荐机器人(db, user)


@router.get("/jiantou-list/", response_model=机器人推荐列表InResponse, description="建投机器人推荐列表")
async def get_jiantou_list(
    标签: str = Query(None),
    trade_date: datetime = Query(None),
    排序: str = Query("累计收益率", regex="^评级|累计服务人数|累计收益率|最大回撤$"),
    排序方式: str = Query("倒序"),
    limit: int = Query(20, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    db_query = {"状态": 机器人状态.已上线}
    if 标签:
        db_query["标签"] = 标签
    result = await 推荐列表(db, db_query, limit, skip, [排序, 排序方式], trade_date, user)
    documents_count = await get_client_robot_count(db, db_query, user)
    page_size = math.ceil(documents_count / limit) if limit > 0 else 1
    return 机器人推荐列表InResponse(数据=result, 总数据量=documents_count, 总页数=page_size)


@router.get("/user/list", response_model=List[str], description="查询机器人作者列表")
async def query_robot_user_list(
    状态: List[机器人状态] = Query([机器人状态.已上线]),
    评级: List[机器人评级] = Query(["A", "B", "C"]),
    limit: int = Query(0, gt=0, description="限制返回的条数"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["机器人:查看", "机器人:查看他人"]),
):
    query = {"状态": {"$in": 状态}, "评级": {"$in": 评级}, "可见模式": "完全公开"}
    return await get_robot_user_list(db, query, limit, skip)
