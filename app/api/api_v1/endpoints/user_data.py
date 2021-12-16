from datetime import datetime

from fastapi import APIRouter, Security, Query
from starlette.background import BackgroundTasks

from app.core.jwt import get_current_user_authorizer
from app.schedulers.message.func import send_equipment_signal_message_task
from app.schema.common import ResultInResponse

router = APIRouter()


@router.get("/message", response_model=ResultInResponse, description="发送订阅消息")
async def send_message_view(
    background_tasks: BackgroundTasks,
    tdate: datetime = Query(None, description="发送时间"),
    user=Security(get_current_user_authorizer(), scopes=["用户:查看"]),
):
    background_tasks.add_task(send_equipment_signal_message_task, tdate=tdate)
    return ResultInResponse()
