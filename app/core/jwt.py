import re
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, Header
from fastapi.security import SecurityScopes
from jwt import PyJWTError

from app import settings
from app.core.errors import (
    InvalidManufacturerAPIReq,
    PermissionDenied,
    TokenValidationError,
)
from app.core.security import verify_password
from app.crud.permission import 获取某用户的所有权限
from app.crud.user import get_user_by_username
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.models.base.token import TokenPayload
from app.schema.user import User


def _get_authorization_token(authorization: str = Header(...)):
    try:
        token_prefix, token = authorization.split(" ")
        try:
            payload = jwt.decode(
                token,
                key=settings.auth.get_rsa_public_key(),
                audience=settings.auth.audience,
                algorithms=settings.auth.algorithm,
            )
        except PyJWTError:
            raise TokenValidationError(message="Token验证失败")
    except ValueError:
        raise TokenValidationError(message="无法解析的Header，检查是否正确设置了认证Header")
    payload.update(token=token)
    return TokenPayload(**payload)


async def _get_current_user(
    db: AsyncIOMotorClient = Depends(get_database),
    token_payload: TokenPayload = Depends(_get_authorization_token),
    security_scopes: SecurityScopes = SecurityScopes(),
) -> User:
    dbuser = await get_user_by_username(db, token_payload.username)
    permissions = await 获取某用户的所有权限(db, dbuser)
    user_security_scopes = [":".join([key, value]).replace("*", ".*") for key in permissions.permissions for value in permissions.permissions[key]]
    token_regex = "|".join(user_security_scopes)
    r = re.compile(token_regex)
    for scope in security_scopes.scopes:
        if not r.match(scope):
            raise PermissionDenied(code="403", message=f"用户权限不足, 需要的权限: {security_scopes.scope_str}")
    user = User(**dbuser.dict())
    return user


def _get_authorization_token_optional(authorization: str = Header(None)):
    if authorization:
        return _get_authorization_token(authorization)
    return ""


async def _get_current_user_optional(
    db: AsyncIOMotorClient = Depends(get_database),
    token_payload: TokenPayload = Depends(_get_authorization_token_optional),
    security_scopes: SecurityScopes = SecurityScopes(),
) -> Optional[User]:
    if token_payload:
        return await _get_current_user(db, token_payload)
    return None


def get_current_user_authorizer(*, required: bool = True):
    if required:
        return _get_current_user
    else:
        return _get_current_user_optional


def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None, source: str = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update(
        {
            "exp": expire,
            "sub": settings.auth.access_token_jwt_subject,
            "aud": settings.auth.audience,
        }
    )
    encoded_jwt = jwt.encode(
        to_encode,
        settings.auth.public_key,
        algorithm=settings.auth.algorithm[0],
    )
    return encoded_jwt


def check_metadata_user_authorizer(username: str = Header(...), secret_key: str = Header(...)) -> None:
    """获取厂商数据源身份认证"""
    if not (username == settings.mfrs.CLIENT_USER and verify_password(settings.mfrs.APP_SECRET, secret_key)):
        raise InvalidManufacturerAPIReq
