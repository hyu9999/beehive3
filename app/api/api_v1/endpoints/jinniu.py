from datetime import date

from fastapi import APIRouter, Path, Query, Security
from starlette.background import BackgroundTasks

from app.core.jwt import check_metadata_user_authorizer
from app.schedulers.cn_collection.func import full_quantity_update_real_data
from app.schema.common import ResultInResponse

router = APIRouter()


@router.post("/{event}", description="金牛事件触发api")
async def deal_with_jinniu_event(
        background_tasks: BackgroundTasks,
        event: str = Path(..., regex=r"^update_cn_collection$"),
        sid: str = Query(None, regex=r"^(01|02|03|04|05|06|07|10|11)$"),
        start: date = Query(None, title="开始时间", description="ISO 8601日期格式的字符串, 如: 2008-09-15。"),
        end: date = Query(None, title="结束时间", description="ISO 8601日期格式的字符串t, 如: 2008-09-15。"),
        collection: str = Query(None, title="集合名称"),
        authorizer=Security(check_metadata_user_authorizer),
):
    if event == "update_cn_collection":
        background_tasks.add_task(
            full_quantity_update_real_data,
            start=start.strftime("%Y-%m-%d") if start else start,
            end=end.strftime("%Y-%m-%d") if end else end,
            col_str=collection,
            sid_str=sid,
        )
    return ResultInResponse()
