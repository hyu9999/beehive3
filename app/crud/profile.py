import re
from typing import Optional

from app.core.errors import NoUserError
from app.crud.user import get_user
from app.db.mongodb import AsyncIOMotorClient
from app.extentions import logger
from app.models import MOBILE_RE
from app.models.base.profile import Profile


async def get_profile_for_user(conn: AsyncIOMotorClient, target_username: str, current_username: Optional[str] = None) -> Profile:
    """ 获取用户的资料 """
    user = await get_user(conn, target_username)
    if not user:
        logger.error(f"没有找到用户：{target_username}")
        raise NoUserError
    if re.match(MOBILE_RE, user.username):
        user.username = f"{user.username[:3]}{'*' * 4}{user.username[-4:]}"

    profile = Profile(**user.dict())

    return profile
