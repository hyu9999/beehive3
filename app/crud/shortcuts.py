from typing import Optional

from pydantic import EmailStr

from app.core.errors import UserAlreadyExist
from app.crud.user import get_user, get_user_by_email, get_user_by_mobile
from app.db.mongodb import AsyncIOMotorClient


async def check_free_user(conn: AsyncIOMotorClient, username: Optional[str] = None, email: Optional[EmailStr] = None, mobile: Optional[str] = None):
    if username:
        user_by_username = await get_user(conn, username)
        if user_by_username:
            raise UserAlreadyExist(message="您输入的帐号已被注册！")
    if email:
        user_by_email = await get_user_by_email(conn, email)
        if user_by_email:
            raise UserAlreadyExist(message="您输入的邮箱号已被注册！")
    if mobile:
        user_by_mobile = await get_user_by_mobile(conn, mobile)
        if user_by_mobile:
            raise UserAlreadyExist(message="您输入的手机号已被注册！")
