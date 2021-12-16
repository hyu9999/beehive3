from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from app import settings

API_KEY_NAME = "access_token"

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_query: str = Security(api_key_query), api_key_header: str = Security(api_key_header)):
    if api_key_query == settings.auth.api_key:
        return api_key_query
    elif api_key_header == settings.auth.api_key:
        return api_key_header
    else:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="API KEY 错误，无法通过认证")
