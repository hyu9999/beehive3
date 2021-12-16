import random
from datetime import date, datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, Body, HTTPException, Path, File, Query, UploadFile, Security
from starlette.responses import StreamingResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST
from stralib import FastTdate

from app.core.jwt import get_current_user_authorizer
from app.crud.file import upload, delete, download_by_name, download_by_id, find, batch_upload, find_one
from app.crud.file import count_documents
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.enums.common import 公共文件类型, 保密文件类型
from app.models.rwmodel import PyObjectId
from app.schema.common import StatusInResponse, TradeDaysInResponse, TradeDateInResponse
from app.service.datetime import get_exist_signal_date

router = APIRouter()


@router.get("/trade/date", response_model=StatusInResponse, description="判断是否是交易日")
async def is_tdate_view(trade_date: date = Query(..., alias="date", description="ISO 8601日期格式的字符串, 如: 2008-09-15。")):
    try:
        result = FastTdate.is_tdate(trade_date)
    except KeyError as e:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"入参错误，详情为：{e}")
    return StatusInResponse(status=result)


@router.get("/trade/date/list", response_model=TradeDaysInResponse, description="获取某段时间内的所有交易日")
async def get_all_tdate_in_given_period(
    start: date = Query(..., description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
    end: date = Query(..., description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
):
    if start > end:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail="入参错误，开始时间大于结束时间")
    start, end = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    result = FastTdate.query_all_tdates(start, end)
    return TradeDaysInResponse(交易日列表=result)


@router.get("/trade/real_tdate", response_model=TradeDateInResponse, description="获取真正的交易日")
async def real_trade_date_view(trade_date: date = Query(..., alias="date", description="ISO 8601日期格式的字符串, 如: 2008-09-15。")):
    end_dt = datetime(trade_date.year, trade_date.month, trade_date.day)
    try:
        real_date = get_exist_signal_date(end_dt)
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"获取交易日错误：{e}")
    return TradeDateInResponse(tdate=real_date.date())


@router.post("/file/upload", description="保密文件上传")
async def upload_file(
    filename: str = Body(None),
    file_type: 保密文件类型 = Body("装备源代码"),
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer()),
) -> Dict[str, str]:
    filename = filename or file.filename
    metadata = {"contentType": file.content_type, "file_type": file_type}
    file_id = await upload(db, filename, file, metadata=metadata)
    return {"filename": filename, "file_id": str(file_id)}


@router.post("/file/upload/public", description="公共文件上传")
async def upload_public_file(
    filename: str = Body(None),
    file_type: 公共文件类型 = Body("用户头像"),
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer()),
) -> Dict[str, str]:
    filename = filename or file.filename
    metadata = {"contentType": file.content_type, "file_type": file_type}
    file_id = await upload(db, filename, file, metadata=metadata)
    return {"filename": filename, "file_id": str(file_id)}


@router.post("/file/reupload", description="文件重新上传")
async def reupload_file(
    filename: str = Body(None),
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(
        get_current_user_authorizer(),
    ),
) -> Dict[str, str]:
    filename = filename or file.filename
    old_file = await find_one(db, {"filename": filename})
    if old_file:
        await delete(db, old_file._id)
    file_id = await upload(db, filename, file)
    return {"filename": filename, "file_id": str(file_id)}


@router.post("/files/upload", description="文件批量上传")
async def batch_upload_file(
    files: List[UploadFile] = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(
        get_current_user_authorizer(),
    ),
) -> List:
    result = await find(db, {"filename": {"$in": [x.filename for x in files]}})
    if result:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"[上传文件失败] 文件名重复")
    id_list = await batch_upload(db, files)
    return [str(x) for x in id_list]


@router.get("/file/download/{file_id}", description="文件下载")
async def download_file(
    file_id: PyObjectId = Path(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    file = await download_by_id(db, file_id)
    return StreamingResponse(file.__iter__(), media_type=file.content_type)


@router.get("/file/download", description="通过文件名下载文件")
async def download_file_by_name(
    filename: str = Query(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    file = await download_by_name(db, filename)
    return StreamingResponse(file.__iter__(), media_type=file.content_type)


@router.get("/airflow/download", description="限定仅airflow权限用户通过文件名下载文件")
async def airflow_download_file_by_name(
    filename: str = Query(...),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer(), scopes=["策略:airflow"]),
):
    file = await download_by_name(db, filename)
    return StreamingResponse(file.__iter__(), media_type=file.content_type)


@router.get("/file/download/{file_id}/public", description="公共文件下载")
async def download_public_file(file_id: PyObjectId = Path(...), db: AsyncIOMotorClient = Depends(get_database)):
    file = await download_by_id(db, file_id)
    if file.metadata and file.metadata["file_type"] in 公共文件类型.__members__:
        return StreamingResponse(file.__iter__(), media_type=file.content_type)
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="无权访问的内容")


@router.get("/file/avatar/robot", description="获取机器人随机头像")
async def download_random_avatar(
    avatar: PyObjectId = Query(None),
    db: AsyncIOMotorClient = Depends(get_database),
    _=Security(get_current_user_authorizer()),
):
    if avatar:
        try:
            file = await download_by_id(db, avatar)
            file_num = await count_documents(db, {"filename": {"$regex": f"^机器人默认头像.*"}})
        except Exception as e:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"[获取机器人默认头像失败]{e}")
        random_index = int(file.filename.replace("机器人默认头像", "")) % file_num + 1
    else:
        random_index = random.randint(1, 10)
    try:
        file = await download_by_name(db, f"机器人默认头像{random_index}")
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"[获取机器人默认头像失败]{e}")
    return {"avatar": file._id.__str__()}
