import math
from datetime import date, datetime
from typing import List, Union, Any

from fastapi import APIRouter, Depends, Query, Body, HTTPException, Security, Path
from starlette.status import HTTP_201_CREATED, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_400_BAD_REQUEST
from stralib import FastTdate

from app.core.errors import NoEquipError, EquipCreateNotAllowed, EquipmentDeleteNotAllowed, RecordDoesNotExist, StrategySignalError
from app.core.jwt import get_current_user_authorizer
from app.crud.client_base import get_client_equipment_count
from app.crud.equipment import (
    查询装备列表,
    查询某个装备的详情,
    更新装备的某个字段,
    新建装备,
    删除某装备,
    获取择时回测信号数据,
    获取择时回测指标数据,
    获取择时回测评级数据,
    获取选股回测信号数据,
    获取选股回测指标数据,
    获取选股回测评级数据,
    获取选股实盘信号数据,
    获取择时实盘信号数据,
    更新装备状态,
    更新包状态,
    获取某数据集选股回测评级详情,
    获取某交易日选股回测指标,
    获取某交易日选股回测信号,
    创建装备实盘回测数据,
    更新装备的运行数据,
    查询是否有该装备,
    查询我的装备列表,
    get_equipment_user_list,
    更新装备,
    获取大类资产配置回测指标数据,
    获取基金定投回测指标数据,
    获取大类资产配置回测信号数据,
    获取基金定投回测信号数据,
    获取大类资产配置回测评级数据,
    获取基金定投回测评级数据,
    获取基金定投实盘信号数据,
    获取大类资产配置实盘信号数据,
    获取某装备最新实盘数据,
    获取某装备实盘指标数据,
    删除某装备实盘回测数据,
)
from app.crud.tag import 新建标签
from app.crud.user import get_user_by_nickname
from app.crud_permissions.equipment import 是否有修改装备权限, 是否有删除装备权限
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.dec import equipment_op_decor
from app.enums.common import 回测评级数据集, 数据库排序
from app.enums.equipment import 装备信号传入方式, 装备可见模式, 装备评级, EquipmentCollectionName, 装备状态, 装备分类_3
from app.enums.tag import TagType
from app.models import EQUIPMENT_SID_RE
from app.models.equipment import (
    择时装备回测评级,
    择时装备回测指标,
    择时装备回测信号,
    选股装备回测指标,
    选股装备回测信号,
    择时装备实盘信号,
    选股装备实盘信号,
    Equipment,
    大类资产配置实盘指标,
    基金定投实盘指标,
    基金定投实盘信号,
    大类资产配置实盘信号,
    大类资产配置回测指标,
    基金定投回测指标,
    基金定投回测信号,
    大类资产配置回测信号,
    大类资产配置回测评级,
    基金定投回测评级,
)
from app.models.equipment import 选股装备回测评级
from app.schema.common import ResultInResponse
from app.schema.equipment import (
    装备InResponse,
    装备InCreate,
    装备InUpdate,
    CandlestickInResponse,
    选股回测详情InResponse,
    择时装备回测信号InCreate,
    选股装备回测信号InCreate,
    选股装备回测指标InCreate,
    择时装备回测指标InCreate,
    择时装备回测评级InCreate,
    选股装备回测评级InCreate,
    择时装备实盘信号InCreate,
    选股装备实盘信号InCreate,
    装备商城列表InResponse,
    装备列表InResponse,
    大类资产配置回测信号InCreate,
    基金定投回测信号InCreate,
    大类资产配置回测指标InCreate,
    大类资产配置回测评级InCreate,
    大类资产配置实盘信号InCreate,
    大类资产配置实盘指标InCreate,
    基金定投回测指标InCreate,
    基金定投回测评级InCreate,
    基金定投实盘信号InCreate,
    基金定投实盘指标InCreate,
    SymbolGradeStrategyWordsInresponse,
    装备状态InUpdate,
    装备运行数据InUpdate,
)
from app.service.candlestick import KDataDiagram
from app.service.datetime import get_early_morning
from app.service.equipment import 生成装备标识符, 装备数量限制, get_grade_strategy_words_by_time
from app.service.permission import check_equipment_permission
from app.service.strategy_data import generate_empty_adam_signal, update_adam_strategy_signal

router = APIRouter()


@router.get("/{sid}", description="查询某装备信息", response_model=装备InResponse)
async def get_equipment_by_sid(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看"]),
):
    check_equipment_permission(sid, user)
    response = await 查询某个装备的详情(db, sid)
    if response:
        return response
    else:
        raise NoEquipError(message=f"没有找到装备sid={sid}")


@router.get("/check_exist/", description="查询某装备是否存在", response_model=ResultInResponse)
async def check_equipment_exist(
    name: str = Query(None),
    sid: str = Query(None, regex=EQUIPMENT_SID_RE),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看"]),
):
    result = await 查询是否有该装备(db, {"$or": [{"名称": name, "状态": {"$nin": ["已删除"]}}, {"标识符": sid}]})
    return ResultInResponse(result=result)


@router.get("/on_and_off/", response_model=List[装备InResponse], description="筛选已上线和已下线的装备")
async def query_on_and_off_equipments(
    排序: str = Query(None),
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    equipment_query = {"状态": {"$in": ["已上线", "已下线"]}}
    try:
        order_by_list = [(x.split("=")[0], int(x.split("=")[1])) for x in 排序.split(",")] if 排序 else [("上线时间", -1)]
        return await 查询装备列表(db, equipment_query, limit, skip, order_by_list, user=user)
    except IndexError as e:
        raise HTTPException(status_code=422, detail=f"查询装备排序参数错误，请输入规定的排序方式。详细错误：{e}")


@router.get("", response_model=Union[List[装备InResponse], 装备列表InResponse], description="查询装备信息列表，根据装备查询的条件返回装备信息")
async def query_equipment_list(
    名称: str = Query(None),
    标识符: List[str] = Query(None, regex=EQUIPMENT_SID_RE),
    英文名: str = Query(None),
    状态: List[装备状态] = Query(None),
    上线时间: List[datetime] = Query(None),
    下线时间: List[datetime] = Query(None),
    分类: List[装备分类_3] = Query(None),
    作者: str = Query(None),
    排序: str = Query(None),
    装备库版本: str = Query(None, description="默认查询3.2的装备，若干需要查询3.3的装备则需要写入版本号"),
    一级分类: str = Query(None),
    二级分类: str = Query(None),
    信号传入方式: 装备信号传入方式 = Query(None),
    可见模式: 装备可见模式 = Query(None),
    评级: 装备评级 = Query(None),
    最近使用时间_开始: datetime = Query(None),
    最近使用时间_结束: datetime = Query(None),
    模糊查询: List[str] = Query(None),
    search_name: str = Query(None),
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    is_paging: bool = Query(False),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    equipment_query = {"名称": 名称, "标识符": 标识符, "英文名": 英文名, "作者": 作者, "信号传入方式": 信号传入方式, "可见模式": 可见模式, "评级": 评级, "装备库版本": 装备库版本, "一级分类": 一级分类, "二级分类": 二级分类}
    if 分类:
        equipment_query["分类"] = {"$in": 分类}
    if 状态:
        equipment_query["状态"] = {"$in": 状态}
    if 上线时间:
        equipment_query["上线时间"] = {"$gte": min(上线时间), "$lte": max(上线时间)}
    if 下线时间:
        equipment_query["下线时间"] = {"$gte": min(下线时间), "$lte": max(下线时间)}
    if 最近使用时间_开始 and 最近使用时间_结束:
        equipment_query["最近使用时间"] = {"$gte": 最近使用时间_开始, "$lte": 最近使用时间_结束}
    if search_name:
        if 模糊查询:
            fuzzy_filters = [{x: {"$regex": f"{search_name}"}} for x in 模糊查询]
        else:
            fuzzy_filters = [{"名称": search_name}, {"标签": {"$in": [search_name]}}]
        equipment_query["$or"] = fuzzy_filters
    try:
        order_by_list = [(x.split("=")[0], int(x.split("=")[1])) for x in 排序.split(",")] if 排序 else [("上线时间", -1)]
        equiments_list = await 查询装备列表(db, equipment_query, limit, skip, order_by_list, user)
        if not is_paging:
            return equiments_list
        documents_count = await get_client_equipment_count(db, equipment_query, user)
        page_size = math.ceil(documents_count / limit) if limit > 0 else 1
        return 装备列表InResponse(数据=equiments_list, 总数据量=documents_count, 总页数=page_size)
    except IndexError as e:
        raise HTTPException(status_code=422, detail=f"查询装备排序参数错误，请输入规定的排序方式。详细错误：{e}")


@router.get("/my/list", response_model=List[Any], description="查询我的创建的装备列表，根据装备查询的条件返回装备信息")
async def query_my_equipment_list(
    筛选: str = Query(None),
    分类: 装备分类_3 = Query(None),
    排序: str = Query("运行天数"),
    排序方式: str = Query("倒序"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    if 排序 not in ["运行天数", "累计产生信号数", "累计服务人数"]:
        raise HTTPException(422, detail="错误的排序类型")
    return await 查询我的装备列表(db, 筛选, 排序, 排序方式, user, 分类=分类)


@router.get("/store/list", response_model=装备商城列表InResponse, description="查询商城内的装备列表")
async def query_store_equipment_list(
    search: str = Query(None, description="全文搜索内容"),
    昵称: List[str] = Query(None),
    分类: 装备分类_3 = Query(None),
    标签: List[str] = Query(None),
    排序: str = Query("上线时间"),
    排序方式: str = Query("倒序"),
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    if 排序 not in ["运行天数", "累计产生信号数", "累计服务人数", "上线时间", "订阅人数"]:
        raise HTTPException(422, detail="错误的排序类型")
    query = {"状态": "已上线", "可见模式": "完全公开", "评级": {"$in": ["A", "B", "C"]}}
    query["分类"] = 分类 if 分类 else {"$in": ["选股", "择时", "风控包", "大类资产配置", "基金定投"]}
    if 标签:
        query["标签"] = {"$in": 标签}
    if search:
        query["$or"] = [{"名称": {"$regex": f"{search}"}}, {"标识符": {"$regex": f"{search}"}}, {"作者": {"$regex": f"{search}"}}]
    if 昵称:
        auths = await get_user_by_nickname(db, 昵称)
        query["作者"] = {"$in": [auth.username for auth in auths]}

    equipment_list = await 查询装备列表(db, query, limit, skip, [(排序, 数据库排序[排序方式].value)], user)
    documents_count = await get_client_equipment_count(db, query, user)
    page_size = math.ceil(documents_count / limit) if limit > 0 else 1
    return 装备商城列表InResponse(数据=equipment_list, 总数据量=documents_count, 总页数=page_size)


@router.post("/new", status_code=HTTP_201_CREATED, description="创建新装备", response_model=装备InResponse)
@equipment_op_decor(EquipCreateNotAllowed)
async def create_equipment(新装备: 装备InCreate, db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["装备:创建"])):
    await 装备数量限制(新装备.分类, user, db)
    is_exist = await 查询是否有该装备(db, {"$or": [{"名称": 新装备.名称, "状态": {"$nin": ["已删除"]}}, {"标识符": 新装备.标识符}]})
    if is_exist == "success":
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备失败，装备名称'{新装备.名称}或标识符{新装备.标识符}''已存在！")
    装备字典 = 新装备.dict()
    if not 新装备.标识符:
        装备字典["标识符"] = await 生成装备标识符(新装备.分类, db)
    装备字典["作者"] = user.username
    装备字典["创建时间"] = datetime.utcnow()
    online_time = get_early_morning() if FastTdate.is_tdate(get_early_morning()) else FastTdate.last_tdate(get_early_morning())
    装备字典["上线时间"] = online_time
    if 装备字典["信号传入方式"] == "源代码传入":
        装备字典["状态"] = "审核中"
        if not 新装备.源代码:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"源代码字段必须传入！")
    elif 装备字典["信号传入方式"] == "手动传入":
        装备字典["状态"] = "已上线"
        # 手动传入时插入一个空信号，避免查不到信号而报错
        empty_signal = generate_empty_adam_signal(online_time)
        try:
            update_adam_strategy_signal(装备字典["标识符"], empty_signal, online_time, online_time)
        except Exception as e:
            raise StrategySignalError(message=f"更新策略数据错误，错误信息：{e}")
    else:
        装备字典["状态"] = "已上线" if 新装备.分类 == "风控包" else "未审核"
    await 新建标签(db, 新装备.标签, TagType.装备)
    return await 新建装备(db, Equipment(**装备字典))


@router.put("/{sid}", description="更新某装备", response_model=装备InResponse)
async def update_equipment(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    装备: 装备InUpdate = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:修改", "装备:修改他人"]),
):
    check_equipment_permission(sid, user)
    await 是否有修改装备权限(sid, user, db)
    return await 更新装备的某个字段(db, sid, 装备)


@router.put("/{sid}/operational", description="更新某装备的运行数据", response_model=ResultInResponse)
async def update_equipment_operational(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    装备: 装备运行数据InUpdate = Body(None, embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:修改", "装备:修改他人"]),
):
    await 是否有修改装备权限(sid, user, db)
    try:
        return await 更新装备的运行数据(db, sid, 装备)
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"[更新装备运行数据失败]{e}")


@router.put("/{sid}/action", description="更新某装备状态")
async def update_equipment_status(
    equipment_state_in_update: 装备状态InUpdate = Body(...),
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:修改", "装备:修改他人"]),
):
    if sid.startswith("11"):
        await 是否有修改装备权限(sid, user, db)
        return await 更新包状态(db, sid, equipment_state_in_update)
    else:
        await 是否有修改装备权限(sid, user, db)
        return await 更新装备状态(db, sid, equipment_state_in_update)


@router.put("/{sid}/offline_reason", description="更新某装备的下线原因")
async def update_offline_reason(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    下线原因: str = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:修改", "装备:修改他人"]),
):
    check_equipment_permission(sid, user)
    await 是否有修改装备权限(sid, user, db)
    装备 = await 查询某个装备的详情(db, sid)
    if 装备.状态 != "已下线":
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"该状态不允许修改下线原因")
    await 更新装备(db, sid, {"下线原因": 下线原因})
    return ResultInResponse()


@router.delete("/{sid}", description="删除某装备", response_description="返回成功删除了的文档个数")
@equipment_op_decor(EquipmentDeleteNotAllowed)
async def delete_a_equipment(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:删除"]),
) -> int:
    await 是否有删除装备权限(sid, user, db)
    result = await 删除某装备(db, sid)
    return result.deleted_count


@router.get("/candlestick/market", response_model=List[CandlestickInResponse], description="指数k线图")
async def candlestick_chart(
    symbol: str = Query("399001", title="指数代码"),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    push_forward: bool = Query(False, description="往前推1个交易日"),
):
    if push_forward:
        start = FastTdate.last_tdate(start)
    data = KDataDiagram(symbol=symbol).market(start, end)
    return [CandlestickInResponse(**x) for x in data]


@router.get("/{sid}/backtest_indicator", description="获取某装备的回测指标", response_model=Union[List[选股装备回测指标], List[择时装备回测指标], List[大类资产配置回测指标], List[基金定投回测指标]])
async def get_equipment_indicator(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    symbol: str = Query("399001", title="指数代码"),
    回测年份: str = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    try:
        if sid.startswith("02"):
            return await 获取选股回测指标数据(db, sid)
        elif sid.startswith("03"):
            return await 获取择时回测指标数据(db, sid, symbol, 回测年份)
        elif sid.startswith("06"):
            return await 获取大类资产配置回测指标数据(db, sid)
        elif sid.startswith("07"):
            return await 获取基金定投回测指标数据(db, sid)
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"暂不支持的sid类型({sid})")
    except HTTPException as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"查询装备({sid})回测指标发生错误，错误信息: {e.detail}")


@router.get("/{sid}/backtest_signal", description="获取某装备的回测信号", response_model=Union[List[选股装备回测信号], List[择时装备回测信号], List[大类资产配置回测信号], List[基金定投回测信号]])
async def get_equipment_signal(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    try:
        start = datetime.combine(start, datetime.min.time())
        end = datetime.combine(end, datetime.min.time())
        if sid.startswith("02"):
            return await 获取选股回测信号数据(db, sid, start, end, limit, skip)
        elif sid.startswith("03"):
            return await 获取择时回测信号数据(db, sid, start, end, limit, skip)
        elif sid.startswith("06"):
            return await 获取大类资产配置回测信号数据(db, sid, start, end, limit, skip)
        elif sid.startswith("07"):
            return await 获取基金定投回测信号数据(db, sid, start, end, limit, skip)
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"暂不支持的sid类型({sid})")
    except HTTPException as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"查询装备({sid})回测信号发生错误，错误信息: {e.detail}")


@router.get("/{sid}/backtest_assess", description="获取某装备的回测评级", response_model=Union[List[选股装备回测评级], List[择时装备回测评级], List[大类资产配置回测评级], List[基金定投回测评级]])
async def get_equipment_assess(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    symbol: str = Query("399001", title="指数代码"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    try:
        if sid.startswith("02"):
            return await 获取选股回测评级数据(db, sid)
        elif sid.startswith("03"):
            return await 获取择时回测评级数据(db, sid, symbol)
        elif sid.startswith("06"):
            return await 获取大类资产配置回测评级数据(db, sid)
        elif sid.startswith("07"):
            return await 获取基金定投回测评级数据(db, sid)
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"暂不支持的sid类型({sid})")
    except HTTPException as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"查询装备({sid})回测评级发生错误，错误信息: {e.detail}")


@router.get("/{sid}/real_signal", description="获取某装备的实盘信号", response_model=Union[List[选股装备实盘信号], List[择时装备实盘信号], List[大类资产配置实盘信号], List[基金定投实盘信号]])
async def get_equipment_real_signal(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    limit: int = Query(20, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    排序: str = Query("交易日期"),
    排序方式: str = Query("正序"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    check_equipment_permission(sid, user)
    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    if sid.startswith("02"):
        return await 获取选股实盘信号数据(db, sid, start, end, limit, skip)
    elif sid.startswith("03"):
        return await 获取择时实盘信号数据(db, sid, start, end, limit, skip)
    elif sid.startswith("06"):
        return await 获取大类资产配置实盘信号数据(db, sid, start, end, limit, skip, [(排序, 数据库排序[排序方式].value)])
    elif sid.startswith("07"):
        return await 获取基金定投实盘信号数据(db, sid, start, end, limit, skip, [(排序, 数据库排序[排序方式].value)])
    else:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"暂不支持的sid类型({sid})")


@router.get("/backtest/details/{sid}", description="获取选股装备的回测评级详情", response_model=选股回测详情InResponse)
async def get_equipment_backtest_details(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    数据集: 回测评级数据集 = Query("测试集评级", description="数据集，包括：测试集评级，训练集评级，整体评级"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    选股装备回测评级 = await 获取某数据集选股回测评级详情(db, sid, 数据集)
    if 选股装备回测评级:
        交易日期 = 选股装备回测评级.结束时间
        选股装备回测指标 = await 获取某交易日选股回测指标(db, sid, 交易日期)
        选股装备回测信号 = await 获取某交易日选股回测信号(db, sid, 交易日期)
        if not all([选股装备回测指标, 选股装备回测信号]):
            raise RecordDoesNotExist(message=f"查询装备({sid})回测信息发生错误")
    else:
        raise RecordDoesNotExist(message=f"查询装备({sid})回测评级发生错误")
    return 选股回测详情InResponse(选股装备回测评级=选股装备回测评级, 选股装备回测指标=选股装备回测指标, 选股装备回测信号=选股装备回测信号)


@router.post("/timings/backtest_signal", description="创建择时装备的回测信号数据", response_model=ResultInResponse)
async def create_timings_backtest_signal(
    装备回测信号数据: List[择时装备回测信号InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备回测信号数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备回测信号失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "择时回测信号collection名", 装备回测信号数据)


@router.post("/screens/backtest_signal", description="创建选股装备的回测信号数据", response_model=ResultInResponse)
async def create_screens_backtest_signal(
    装备回测信号数据: List[选股装备回测信号InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备回测信号数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备回测信号失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "选股回测信号collection名", 装备回测信号数据)


@router.post("/timings/backtest_indicator", description="创建择时装备的回测指标数据", response_model=ResultInResponse)
async def create_timings_backtest_indicator(
    装备回测指标数据: List[择时装备回测指标InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备回测指标数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备回测指标失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "择时回测指标collection名", 装备回测指标数据)


@router.post("/screens/backtest_indicator", description="创建选股装备的回测指标数据", response_model=ResultInResponse)
async def create_screens_backtest_indicator(
    装备回测指标数据: List[选股装备回测指标InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备回测指标数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备回测指标失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "选股回测指标collection名", 装备回测指标数据)


@router.post("/timings/backtest_assess", description="创建择时装备的回测评级数据", response_model=ResultInResponse)
async def create_timings_backtest_assess(
    装备回测评级数据: List[择时装备回测评级InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备回测评级数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备回测评级失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "择时回测评级collection名", 装备回测评级数据)


@router.post("/screens/backtest_assess", description="创建选股装备的回测评级数据", response_model=ResultInResponse)
async def create_screens_backtest_assess(
    装备回测评级数据: List[选股装备回测评级InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备回测评级数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备回测评级失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "选股回测评级collection名", 装备回测评级数据)


@router.post("/timings/real_signal", description="创建择时装备的实盘信号数据", response_model=ResultInResponse)
async def create_timings_real_signal(
    装备实盘信号数据: List[择时装备实盘信号InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备实盘信号数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备实盘信号失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "择时实盘信号collection名", 装备实盘信号数据)


@router.post("/screens/real_signal", description="创建选股装备的实盘信号数据", response_model=ResultInResponse)
async def create_screens_real_signal(
    装备实盘信号数据: List[选股装备实盘信号InCreate] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    if not 装备实盘信号数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备实盘信号失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, "选股实盘信号collection名", 装备实盘信号数据)


@router.get("/user/list", response_model=List[str], description="查询装备作者列表")
async def query_equipment_user_list(
    状态: List[装备状态] = Query([装备状态.已上线]),
    评级: List[装备评级] = Query(["A", "B", "C"]),
    limit: int = Query(0, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    query = {"状态": {"$in": 状态}, "评级": {"$in": 评级}, "可见模式": "完全公开"}
    return await get_equipment_user_list(db, query, limit, skip)


@router.get("/{sid}/real_indicator", description="查询大类资产/基金定投装备实盘指标数据", response_model=List[Union[大类资产配置实盘指标, 基金定投实盘指标]])
async def get_latest_equipment_real_indicator(
    sid: str = Path(..., regex="^(06|07)", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    limit: int = Query(0, ge=0, description="限制返回的条数，0=全部"),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    return await 获取某装备实盘指标数据(db, sid, start, end, limit, skip)


@router.get("/{sid}/{real_type}/latest", description="查询某装备最新实盘数据", response_model=Union[大类资产配置实盘指标, 基金定投实盘指标, List[大类资产配置实盘信号], List[基金定投实盘信号]])
async def get_latest_equipment_real_data(
    sid: str = Path(..., regex="^(06|07)", min_length=14, max_length=14),
    real_type: str = Path(..., regex="^(real_signal|real_indicator)$"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    return await 获取某装备最新实盘数据(db, sid, real_type)


@router.post("/{equipment_name}/{data_type}", description="创建装备的实盘回测数据", response_model=ResultInResponse)
async def create_cn_data(
    equipment_name: str = Path(..., regex="^(asset_allocation|aipman)$"),
    data_type: str = Path(..., regex="^(backtest_signal|backtest_indicator|backtest_assess|real_signal|real_indicator)$"),
    装备实盘回测数据: List[
        Union[
            择时装备回测信号InCreate,
            择时装备回测指标InCreate,
            择时装备回测评级InCreate,
            择时装备实盘信号InCreate,
            选股装备回测信号InCreate,
            选股装备回测指标InCreate,
            选股装备回测评级InCreate,
            大类资产配置回测信号InCreate,
            大类资产配置回测指标InCreate,
            大类资产配置回测评级InCreate,
            大类资产配置实盘信号InCreate,
            大类资产配置实盘指标InCreate,
            基金定投回测信号InCreate,
            基金定投回测指标InCreate,
            基金定投回测评级InCreate,
            基金定投实盘信号InCreate,
            基金定投实盘指标InCreate,
        ]
    ] = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    collection_name = EquipmentCollectionName[equipment_name].value[data_type].value
    if not 装备实盘回测数据:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"创建装备回测信号失败，错误原因：传入列表不能为空")
    return await 创建装备实盘回测数据(db, collection_name, 装备实盘回测数据)


@router.delete("/{equipment_name}/{data_type}/{sid}", description="删除某装备的实盘回测数据", response_model=ResultInResponse)
async def delete_cn_data(
    equipment_name: str = Path(..., regex="^(screens|timings|asset_allocation|aipman)$"),
    data_type: str = Path(..., regex="^(backtest_signal|backtest_indicator|backtest_assess|real_signal|real_indicator)$"),
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    collection_name = EquipmentCollectionName[equipment_name].value[data_type].value
    return await 删除某装备实盘回测数据(db, collection_name, sid)


@router.get("/stocks/grade_list", description="查询风控包装备股票池风险等级策略话术列表", response_model=List[SymbolGradeStrategyWordsInresponse])
async def get_grade_strategy_words_by_time_view(
    sid: str = Query(..., regex=r"^(11)[\d]{6}[\w]{4}[\d]{2}$", description="风控包标识符"),
    symbol_list: List[str] = Query(..., description="股票基本信息"),
    start: datetime = Query(None, description="开始时间"),
    end: datetime = Query(None, description="结束时间"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:查看", "装备:查看他人"]),
):
    check_equipment_permission(sid, user)
    equipment = await 查询某个装备的详情(db, sid)
    return await get_grade_strategy_words_by_time(
        db, equipment.装备列表, symbol_list, start.strftime("%Y%m%d") if start else None, end.strftime("%Y%m%d") if start else None
    )


@router.put("/{sid}/latest", description="更新装备最近使用时间")
async def update_equipment_last_used_time_view(
    sid: str = Path(...),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["装备:修改", "装备:修改他人"]),
):
    result = await 更新装备(db, 标识符=sid, 装备={"最近使用时间": datetime.utcnow()})
    return ResultInResponse(result="更新成功" if result.modified_count == 1 else "更新失败")
