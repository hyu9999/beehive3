from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.enums.user import 用户状态
from app.models import MOBILE_RE, PASSWORD_RE
from app.models.base.user import 厂商基本信息, 用户基本信息
from app.models.rwmodel import PyObjectId, RWModel
from app.models.user import UserMessage
from app.schema.base import 分页Response
from app.schema.common import KeyValueInResponse
from app.schema.portfolio import PortfolioInResponse


class User(用户基本信息):
    client_name: str = Field(None, title="厂商名称")
    client: 厂商基本信息 = Field(None, title="厂商用户")
    id: PyObjectId


class UserInResponse(User):
    pass


class LoginInResponse(RWModel):
    user: User = Field(None, title="用户信息")
    token: str = Field(None, title="token")
    registration_required: bool = Field(False, title="是否需要注册")


class UserInCreate(BaseModel):
    mobile: str = Field(..., title="手机", regex=MOBILE_RE)
    username: str = Field(..., min_length=3, max_length=60)
    email: EmailStr = Field(None, title="邮箱")
    password: str = Field("", regex=PASSWORD_RE)
    nickname: str = Field(None, title="昵称")


class UserInRegister(UserInCreate):
    username: str = Field(None, min_length=3, max_length=60)
    password: str = Field(..., regex=PASSWORD_RE)


class ManufacturerUserInCreate(BaseModel):
    username: str
    client_name: Optional[str]
    app_secret: str
    mobile: str = Field(..., title="手机", regex=MOBILE_RE)
    client: 厂商基本信息 = Field(厂商基本信息(), title="厂商用户")


class UserInLogin(BaseModel):
    username: str = Field(None, title="用户名")
    mobile: str = Field(None, title="手机", regex=MOBILE_RE)
    api_key: str = Field(None, title="第三方用户调用认证标识")
    app_secret: str = Field(None, title="厂商用户认证标识")


class WebUserInLogin(BaseModel):
    mobile: str = Field(..., title="手机", regex=MOBILE_RE)
    password: str = Field(..., title="密码")


class SMSLogin(BaseModel):
    mobile: str = Field(..., title="手机", regex=MOBILE_RE)
    code: str = Field(..., title="验证码")


class UserInSSO(RWModel):
    id: PyObjectId = None
    username: str = None
    email: EmailStr = None


class UserInUpdate(用户基本信息):
    username: Optional[str] = None
    status: 用户状态 = Field(None, title="状态")


class ManufacturerUserInUpdate(RWModel):
    client_name: Optional[str]
    app_secret: Optional[str]
    client: 厂商基本信息 = Field(None, title="厂商用户")


class UserInUpdatePwd(RWModel):
    mobile: str = Field(..., title="手机", regex=MOBILE_RE)
    password: str = Field(..., regex=PASSWORD_RE)


class UserMessageInCreate(UserMessage):
    pass


class UserMessagenInResponse(UserMessage):
    pass


class UserMessageListInResponse(分页Response):
    数据: List[UserMessagenInResponse]


class TargetDataInResponse(RWModel):
    data_list: List[float]


class UserPortfolioTargetInResponse(RWModel):
    portfolio: PortfolioInResponse
    user: User
    data: List[KeyValueInResponse]
