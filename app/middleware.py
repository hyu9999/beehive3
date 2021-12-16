from pymongo.errors import OperationFailure, ConnectionFailure
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST

from app.core.errors import DataBaseError
from app.extentions import logger


class DBErrorMiddleware(BaseHTTPMiddleware):
    """数据库异常处理中间件"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"[数据库异常] {e}")
            return JSONResponse({"message": DataBaseError.message, "code": DataBaseError.code}, status_code=HTTP_400_BAD_REQUEST)
