from pydantic import EmailStr, Field

from app.models.rwmodel import RWModel


class TokenPayload(RWModel):
    username: str
    nickname: str = Field(None, title="昵称")
    mobile: str = Field(None, title="手机", alias="phone")
    email: EmailStr = Field(None, title="邮箱")
    token: str


