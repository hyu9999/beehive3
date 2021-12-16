from pydantic import Field

from app.models.rwmodel import RWModel, PyObjectId


class TokenResponse(RWModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: str
    scope: str
    id_token: str
    id: PyObjectId = Field(None, title="用户id")
    username: str = Field(None, title="账号")
