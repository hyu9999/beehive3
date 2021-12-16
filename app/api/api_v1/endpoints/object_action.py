"""获取对象列表和其支持的操作"""

from typing import List

from fastapi import APIRouter, Security

from app.core.jwt import get_current_user_authorizer
from app.models import object_action

router = APIRouter()


@router.get("", response_model=List[object_action.ObjectAction])
async def get_all_object_and_actions(user=Security(get_current_user_authorizer(), scopes=["对象和操作:查看"])):
    response = []
    for name, obj in object_action.__dict__.items():
        if isinstance(obj, object_action.ObjectAction):
            response.append(obj)
    return response
