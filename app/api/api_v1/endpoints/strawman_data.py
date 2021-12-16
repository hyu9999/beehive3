from datetime import datetime, date

import pandas as pd
from fastapi import APIRouter, Query, Path, Security, Depends
from fastapi import HTTPException

from app.core.jwt import get_current_user_authorizer
from app.crud.equipment import 获取某装备的信号, 查询某个装备的详情
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.enums.common import 数据库排序
from app.models import EQUIPMENT_SID_RE
from app.models.base.strawman_data import TimeSeriesResponseTemplate, 装备信号数量, 装备信号中某股票数量
from app.schema.strawman_data import 择时装备信号列表, 选股装备信号列表, 风控装备信号列表, 风控装备信号数量
from app.service.permission import check_equipment_permission
from app.service.strawman_data import 获取选股信号列表, 获取择时信号列表, 获取风控信号列表, 获取某指数择时信号, 获取风控包最新信号, 获取风控信号数量

router = APIRouter()


@router.get("/signals/screens/{sid}", description="查询某选股装备信号", response_model=TimeSeriesResponseTemplate[选股装备信号列表])
async def get_a_screen_signal_by_sid(
    sid: str = Path(..., regex="^02", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    排序方式: str = Query("倒序", title="排序方式", description="排序方式,包含：'正序','倒序'"),
    format: str = Query("list", title="返回格式", description="支持list和dict两种json格式，list则是一个记录一行，数据放入list_data字段，dict则是以日期为索引把记录做了分组，数据放入dict_data字段。"),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    ascending = True if 数据库排序[排序方式].value == 1 else False
    try:
        check_equipment_permission(sid, user)
        start = datetime.combine(start, datetime.min.time())
        end = datetime.combine(end, datetime.min.time())
        result = await 获取选股信号列表(sid, start, end)
        if not result.empty:
            result.sort_values(ascending=ascending, by="TDATE", inplace=True)
            result.index = result.TDATE
        if format == "list":
            return TimeSeriesResponseTemplate[选股装备信号列表](list_data=result.to_dict(orient="records"))
        elif format == "dict":
            response = {}
            for index, row in result.iterrows():
                if index.date() in response:
                    response[index.date()].append(选股装备信号列表(**row.to_dict()))
                else:
                    response[index.date()] = []
                    response[index.date()].append(选股装备信号列表(**row.to_dict()))
            return TimeSeriesResponseTemplate[选股装备信号列表](dict_data=response)
        else:
            raise RuntimeError("format参数错误，必须是'list'或'dict'!")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"查询失败，原因{e}")


@router.get("/signals/timings/{sid}", description="查询某择时装备指数信号", response_model=TimeSeriesResponseTemplate[择时装备信号列表])
async def get_a_timing_signal_by_sid(
    sid: str = Path(..., regex="^03", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    symbol: str = Query(None, title="指数代码", description="指数代码"),
    排序方式: str = Query("倒序", title="排序方式", description="排序方式，包含：'正序','倒序'"),
    format: str = Query("list", title="返回格式", description="支持list和dict两种json格式，list则是一个记录一行，数据放入list_data字段，dict则是以日期为索引把记录做了分组，数据放入dict_data字段。"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    check_equipment_permission(sid, user)
    ascending = True if 数据库排序[排序方式].value == 1 else False
    try:
        start = datetime.combine(start, datetime.min.time())
        end = datetime.combine(end, datetime.min.time())
        equipment = await 查询某个装备的详情(db, sid)
        if symbol:
            result = await 获取某指数择时信号(sid, start, end, symbol)
            result.sort_values(ascending=ascending, by="信号日期", inplace=True)
        else:
            result = await 获取择时信号列表(sid, start, end, equipment.指数列表)
            result.sort_values(ascending=ascending, by="信号日期", inplace=True)

        if format == "list":
            return TimeSeriesResponseTemplate[择时装备信号列表](list_data=result.to_dict(orient="records"))
        elif format == "dict":
            response = {}
            for index, row in result.iterrows():
                if index.date() in response:
                    response[index.date()].append(择时装备信号列表(**row.to_dict()))
                else:
                    response[index.date()] = []
                    response[index.date()].append(择时装备信号列表(**row.to_dict()))
            return TimeSeriesResponseTemplate[择时装备信号列表](dict_data=response)
        else:
            raise RuntimeError("format参数错误，必须是'list'或'dict'!")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"查询失败，原因{e}")


@router.get("/signals/risks/{sid}", description="查询某风控装备信号", response_model=TimeSeriesResponseTemplate[风控装备信号列表])
async def get_a_risk_signal_by_sid(
    sid: str = Path(..., regex="^04", min_length=14, max_length=14),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    format: str = Query("list", title="返回格式", description="支持list和dict两种json格式，list则是一个记录一行，数据放入list_data字段，dict则是以日期为索引把记录做了分组，数据放入dict_data字段。"),
):
    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    result = await 获取风控信号列表(sid, start, end)
    if not result.empty:
        result.sort_values(ascending=False, by="tdate", inplace=True)
        result.index = result.tdate
    if format == "list":
        return TimeSeriesResponseTemplate[风控装备信号列表](list_data=result.to_dict(orient="records"))
    elif format == "dict":
        response = {}
        for index, row in result.iterrows():
            if index.date() in response:
                response[index.date()].append(风控装备信号列表(**row.to_dict()))
            else:
                response[index.date()] = []
                response[index.date()].append(风控装备信号列表(**row.to_dict()))
        return TimeSeriesResponseTemplate[风控装备信号列表](dict_data=response)
    else:
        raise HTTPException(status_code=400, detail="format参数错误，必须是'list'或'dict'!")


@router.get("/signals/numbers/{sid}", description="查询某装备信号数量", response_model=TimeSeriesResponseTemplate[装备信号数量])
async def get_a_number_signal_by_sid(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    format: str = Query("list", title="返回格式", description="支持list和dict两种json格式，list则是一个记录一行，数据放入list_data字段，dict则是以日期为索引把记录做了分组，数据放入dict_data字段。"),
    _=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    try:
        start = datetime.combine(start, datetime.min.time())
        end = datetime.combine(end, datetime.min.time())
        result = await 获取某装备的信号(sid, start, end)
        equipment_numbers = {"标识符": sid, "开始时间": start, "结束时间": end, "信号数量": result.query("symbol != 'nan'").shape[0]}
        from pandas import DataFrame

        equipment_numbers_df = DataFrame(equipment_numbers, index=[sid])
        if format == "list":
            return TimeSeriesResponseTemplate[装备信号数量](list_data=equipment_numbers_df.to_dict(orient="records"))
        elif format == "dict":
            response = {}
            for index, row in equipment_numbers_df.iterrows():
                if row.结束时间 in response:
                    response[row.结束时间].append(装备信号数量(**row.to_dict()))
                else:
                    response[row.结束时间] = []
                    response[row.结束时间].append(装备信号数量(**row.to_dict()))
            return TimeSeriesResponseTemplate[装备信号数量](dict_data=response)
        else:
            raise RuntimeError("format参数错误，必须是'list'或'dict'!")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"查询失败，原因{e}")


@router.get(
    "/signals/symbol_numbers/{sid}",
    description="查询装备信号中某股票数量",
    response_model=TimeSeriesResponseTemplate[装备信号中某股票数量],
)
async def get_symbol_number_signal_by_sid(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    symbol: str = Query(..., title="股票代码"),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    format: str = Query("list", title="返回格式", description="支持list和dict两种json格式，list则是一个记录一行，数据放入list_data字段，dict则是以日期为索引把记录做了分组，数据放入dict_data字段。"),
    _=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    try:
        start = datetime.combine(start, datetime.min.time())
        end = datetime.combine(end, datetime.min.time())
        cal_num = 0
        result = await 获取某装备的信号(sid, start, end)
        if "SYMBOL" in result.columns:
            cal_num = result.query("SYMBOL == @symbol").shape[0]
        elif "symbol" in result.columns:
            cal_num = result.query("symbol in @symbol").shape[0]
        equipment_numbers = [{"标识符": sid, "证券代码": symbol, "开始时间": start, "结束时间": end, "出现次数": cal_num}]
        from pandas import DataFrame

        equipment_numbers_df = DataFrame(equipment_numbers)
        if format == "list":
            return TimeSeriesResponseTemplate[装备信号中某股票数量](list_data=equipment_numbers_df.to_dict(orient="records"))
        elif format == "dict":
            response = {}
            for index, row in equipment_numbers_df.iterrows():
                if row.结束时间 in response:
                    response[row.结束时间].append(装备信号中某股票数量(**row.to_dict()))
                else:
                    response[row.结束时间] = []
                    response[row.结束时间].append(装备信号中某股票数量(**row.to_dict()))
            return TimeSeriesResponseTemplate[装备信号中某股票数量](dict_data=response)
        else:
            raise RuntimeError("format参数错误，必须是'list'或'dict'!")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"查询失败，原因{e}")


@router.get(
    "/package/signals/numbers/{sid}",
    description="查询某风控包装备信号数量",
    response_model=TimeSeriesResponseTemplate[风控装备信号数量],
)
async def get_package_signals_number_by_sid(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    start: date = Query(..., title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
    format: str = Query("list", title="返回格式", description="支持list和dict两种json格式，list则是一个记录一行，数据放入list_data字段，dict则是以日期为索引把记录做了分组，数据放入dict_data字段。"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    check_equipment_permission(sid, user)
    try:
        start = datetime.combine(start, datetime.min.time())
        end = datetime.combine(end, datetime.min.time())
        package = await 查询某个装备的详情(db, sid)
        response_result = [
            {"标识符": eq_sid, "开始时间": start, "结束时间": end, "装备名称": (await 查询某个装备的详情(db, eq_sid)).名称, "信号数量": await 获取风控信号数量(eq_sid, start, end)}
            for eq_sid in package.装备列表
        ]
        response_df = pd.DataFrame(response_result)
        if format == "list":
            return TimeSeriesResponseTemplate[风控装备信号数量](list_data=response_df.to_dict(orient="records"))
        elif format == "dict":
            response = {}
            for index, row in response_df.iterrows():
                if row.结束时间 in response:
                    response[row.结束时间].append(风控装备信号数量(**row.to_dict()))
                else:
                    response[row.结束时间] = []
                    response[row.结束时间].append(风控装备信号数量(**row.to_dict()))
            return TimeSeriesResponseTemplate[风控装备信号数量](dict_data=response)
        else:
            raise RuntimeError("format参数错误，必须是'list'或'dict'!")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"查询失败，原因{e}")


@router.get(
    "/package/signals/numbers/{sid}/latest",
    description="查询某风控包装备最新信号",
    response_model=TimeSeriesResponseTemplate[风控装备信号数量],
)
async def get_package_signals_number_by_sid(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    format: str = Query("list", title="返回格式", description="支持list和dict两种json格式，list则是一个记录一行，数据放入list_data字段，dict则是以日期为索引把记录做了分组，数据放入dict_data字段。"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["稻草人数据:查看"]),
):
    check_equipment_permission(sid, user)
    try:
        response_result, 交易日期 = await 获取风控包最新信号(sid, db)
        if not 交易日期:
            return None
        response_df = pd.DataFrame(response_result)
        if format == "list":
            return TimeSeriesResponseTemplate[风控装备信号数量](交易日期=交易日期, list_data=response_df.to_dict(orient="records"))
        elif format == "dict":
            response = {}
            for index, row in response_df.iterrows():
                if row.结束时间 in response:
                    response[row.结束时间].append(风控装备信号数量(**row.to_dict()))
                else:
                    response[row.结束时间] = []
                    response[row.结束时间].append(风控装备信号数量(**row.to_dict()))
            return TimeSeriesResponseTemplate[风控装备信号数量](dict_data=response)
        else:
            raise RuntimeError("format参数错误，必须是'list'或'dict'!")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"查询失败，原因{e}")
