from typing import List

from app.enums.object_action import Action
from app.models.rwmodel import RWModel


class 对象行为基本信息(RWModel):
    url_prefix: str
    name: str
    actions: List[Action]
