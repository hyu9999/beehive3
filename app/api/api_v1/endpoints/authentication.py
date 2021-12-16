from datetime import timedelta

from fastapi import APIRouter, Body, Depends

from app import settings
from app.core.errors import LoginError, SMSSendError
from app.core.jwt import create_access_token
from app.crud.user import get_user_by_mobile, get_user_by_username
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.global_var import G
from app.models import MOBILE_RE
from app.outer_sys.message.adaptor.sms import SendSMS
from app.outer_sys.message.send_msg import SendMessage
from app.outer_sys.message.utils import verify_code
from app.schema.authentication import TencentSMSInResponse
from app.schema.common import ResultInResponse
from app.schema.user import LoginInResponse, User, UserInLogin, WebUserInLogin, SMSLogin
from app.settings.base import GlobalConfig, get_settings

router = APIRouter()


@router.post("/login", response_model=LoginInResponse, description="登录")
async def login_view(
    user: UserInLogin = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    settings: GlobalConfig = Depends(get_settings),
):
    if user.username:
        dbuser = await get_user_by_username(db, user.username)
        if not dbuser:
            raise LoginError(message=f"用户名为{user.username}的用户不存在")
    else:
        dbuser = await get_user_by_mobile(db, user.mobile)
        if not dbuser:
            raise LoginError(message=f"手机号为{user.mobile}的用户不存在")
    if "厂商用户" in dbuser.roles:
        if not user.app_secret or not dbuser.check_app_secret(user.app_secret):
            raise LoginError(message="错误的app_secret")
    else:
        if not user.api_key or not user.api_key == settings.auth.api_key:
            raise LoginError(message="错误的api_key")
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(
        data={"mobile": dbuser.mobile, "username": dbuser.username},
        expires_delta=access_token_expires,
    )
    return LoginInResponse(token=token, user=User(**dbuser.dict()))


@router.post("/web_login", response_model=LoginInResponse, description="前端登录")
async def login_view(
    user: WebUserInLogin = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    settings: GlobalConfig = Depends(get_settings),
):
    dbuser = await get_user_by_mobile(db, user.mobile)
    if not dbuser:
        raise LoginError(message=f"手机号为{user.mobile}的用户不存在")
    if not user.password or not dbuser.check_password(user.password):
        raise LoginError(message="错误的密码")
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(
        data={"mobile": dbuser.mobile, "username": dbuser.username},
        expires_delta=access_token_expires,
    )
    return LoginInResponse(token=token, user=User(**dbuser.dict()))


@router.post("/code", response_model=TencentSMSInResponse, description="短信验证码")
async def send_sms_view(
    mobile: str = Body(..., embed=True, regex=MOBILE_RE),
):
    if not settings.sms.switch:
        return TencentSMSInResponse(mobile=mobile, sms_code=settings.sms.fixed_code)
    sm = SendMessage(SendSMS())
    # 验证码未过期
    redis_key = f"sms_{mobile}"
    redis_value = await G.cache.get(redis_key)
    if redis_value:
        raise SMSSendError(message="验证码获取频繁，请稍后重试")
    # 发送消息
    rsp = sm.send_code(mobile=mobile)
    # 将验证码放在缓存中
    await G.cache.set(redis_key, rsp["sms_code"], settings.sms.expire * 60)
    return TencentSMSInResponse(**rsp)


@router.post("/verify_code", response_model=ResultInResponse, description="短信验证码")
async def verify_code_view(
    mobile: str = Body(..., embed=True, regex=MOBILE_RE),
    code: str = Body(..., embed=True),
):
    await verify_code(mobile, code)
    return ResultInResponse()


@router.post("/sms_login", response_model=LoginInResponse, description="短信验证码")
async def login_with_sms_view(
    user: SMSLogin = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
):
    dbuser = await get_user_by_mobile(db, user.mobile)
    await verify_code(user.mobile, user.code)
    if not dbuser:
        return LoginInResponse(registration_required=True)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(
        data={"mobile": dbuser.mobile, "username": dbuser.username},
        expires_delta=access_token_expires,
    )
    return LoginInResponse(token=token, user=User(**dbuser.dict()))
