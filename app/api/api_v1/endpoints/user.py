from datetime import timedelta, date, datetime
from typing import List, Union, Dict

from fastapi import APIRouter, Body, Depends, Security, Path, Query
from starlette.status import HTTP_201_CREATED

from app import settings
from app.core.errors import (
    NoUserError,
    PermissionDenied,
    NoEquipError,
    EquipCanNotBeSubscribed,
    RobotCanNotBeSubscribed,
    NoPortfolioError,
    PortfolioCanNotBeSubscribed,
    VIPCodeError,
    UpgradeVIPError, ParamsError,
)
from app.core.jwt import get_current_user_authorizer, create_access_token
from app.crud.equipment import 查询某个装备的详情
from app.crud.permission import 获取某用户的所有权限
from app.crud.portfolio import get_portfolio_by_id
from app.crud.robot import 查询某机器人信息, check_strategy_exist
from app.crud.shortcuts import check_free_user
from app.crud.user import (
    update_user,
    create_user,
    update_pwd,
    get_user,
    订阅装备,
    订阅机器人,
    取消订阅装备,
    取消订阅机器人,
    获取某用户消息列表,
    创建消息,
    get_user_by_mobile,
    update_user_roles,
    delete_user,
    subscribe_portfolio,
    unsubscribe_portfolio,
    read_user_message,
    update_app_secret,
    get_user_by_username,
    get_manufacturer_user,
    update_manufacturer_user,
    create_manufacturer_user,
    delete_manufacturer_user,
)
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.enums.common import 数据库排序, 产品分类
from app.enums.equipment import 装备状态, 装备分类_3
from app.enums.portfolio import 组合状态
from app.enums.robot import 机器人状态
from app.enums.user import 消息分类
from app.models import EQUIPMENT_SID_RE, MOBILE_RE
from app.models.rwmodel import PyObjectId
from app.schema.common import ResultInResponse, StatusInResponse, KeyValueInResponse
from app.schema.user import (
    User,
    UserInResponse,
    UserInUpdate,
    UserInUpdatePwd,
    UserMessageListInResponse,
    UserMessageInCreate,
    UserInCreate,
    UserPortfolioTargetInResponse,
    ManufacturerUserInCreate,
    UserInRegister,
    LoginInResponse,
)
from app.service.create_limit import 创建数量限制
from app.service.permission import check_robot_permission, check_equipment_permission
from app.service.portfolio.portfolio_target import get_user_portfolio_targets

router = APIRouter()


@router.get("", response_model=UserInResponse, description="查询用户")
async def get_view(
    username: str = Query(None, description="用户名"), user: User = Depends(get_current_user_authorizer()), db: AsyncIOMotorClient = Depends(get_database)
):
    if not username:
        return UserInResponse(**user.dict())
    query_user = await get_user(db, username)
    if query_user:
        return UserInResponse(**query_user.dict())
    raise NoUserError


@router.get("/check_exist/", response_model=ResultInResponse)
async def check_exist_get_view(
    username: str = Query(None, description="账户"),
    mobile: str = Query(None, regex=MOBILE_RE),
    db: AsyncIOMotorClient = Depends(get_database),
):
    if username:
        dbuser = await get_user(db, username)
    elif mobile:
        dbuser = await get_user_by_mobile(db, mobile)
    else:
        raise ParamsError
    if not dbuser:
        return ResultInResponse(result="failed")
    return ResultInResponse()


@router.post("/register", response_model=LoginInResponse, status_code=HTTP_201_CREATED)
async def register_view(user: UserInRegister = Body(..., embed=True), db: AsyncIOMotorClient = Depends(get_database)):
    params = user.dict(include={"username", "email", "mobile"})
    await check_free_user(db, **params)
    async with await db.start_session() as s:
        async with s.start_transaction():
            user.username = user.username if user.username else user.mobile
            user.nickname = user.nickname if user.nickname else f"用户{user.mobile[-4:]}"
            dbuser = await create_user(db, user)
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            token = create_access_token(
                data={"mobile": dbuser.mobile, "username": dbuser.username},
                expires_delta=access_token_expires,
            )
            return LoginInResponse(token=token, user=User(**dbuser.dict()))


@router.post("", response_model=ResultInResponse, status_code=HTTP_201_CREATED)
async def create_view(
    user: UserInCreate = Body(..., embed=True), super_user=Security(get_current_user_authorizer()), db: AsyncIOMotorClient = Depends(get_database)
):
    if "超级用户" not in super_user.roles:
        raise PermissionDenied
    params = user.dict(include={"username", "email", "mobile"})
    await check_free_user(db, **params)
    if not user.nickname:
        user.nickname = f"用户{user.mobile[-4:]}"

    async with await db.start_session() as s:
        async with s.start_transaction():
            await create_user(db, user)
            return ResultInResponse()


@router.delete("/{username}", response_model=ResultInResponse)
async def delete_view(username: str = Path(...), user=Security(get_current_user_authorizer()), db: AsyncIOMotorClient = Depends(get_database)):
    if "超级用户" not in user.roles:
        raise PermissionDenied
    await delete_user(db, username)
    return ResultInResponse()


@router.put("", response_model=UserInResponse)
async def update_view(
    user: UserInUpdate = Body(..., embed=True),
    current_user: User = Security(get_current_user_authorizer(), scopes=["用户:修改"]),
    db: AsyncIOMotorClient = Depends(get_database),
):
    if user.username == current_user.username:
        user.username = None
    if user.email == current_user.email:
        user.email = None

    await check_free_user(db, user.username, user.email)

    dbuser = await update_user(db, current_user.username, user)
    return UserInResponse(**dbuser.dict())


@router.put("/forget", response_model=ResultInResponse)
async def forget_pwd_view(
    user: UserInUpdatePwd = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
):
    """
    忘记密码
    """
    dbuser = await get_user_by_mobile(db, user.mobile)
    if not dbuser:
        raise NoUserError(message=f"您输入的手机号'{user.mobile}'尚未注册，请先注册！")
    await update_pwd(db, user.password, dbuser)
    return ResultInResponse()


@router.put("/password", response_model=ResultInResponse)
async def update_pwd_view(
    user: UserInUpdatePwd = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    current_user=Security(get_current_user_authorizer(), scopes=["用户:修改"]),
):
    """
    修改密码
    """
    if current_user.mobile != user.mobile:
        raise PermissionDenied()
    dbuser = await get_user_by_mobile(db, user.mobile)
    if not dbuser:
        raise NoUserError(message=f"您输入的手机号'{user.mobile}'尚未注册，请先注册！")
    await update_pwd(db, user.password, dbuser)
    await update_app_secret(db, user.password, dbuser)
    return ResultInResponse()


@router.put("/app_secret", response_model=ResultInResponse)
async def app_secret_action_view(
    app_secret: str = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    user: User = Security(get_current_user_authorizer(), scopes=["用户:修改"]),
):
    """
    修改app_secret
    """
    dbuser = await get_user_by_username(db, user.username)
    if not dbuser:
        raise NoUserError(message=f"您输入的用户'{user.username}'尚未注册，请先注册！")
    await update_app_secret(db, app_secret, dbuser)
    return ResultInResponse()


@router.get("/refresh", response_model=Dict[str, str])
async def refresh_token_get_view(current_user: User = Security(get_current_user_authorizer()), db: AsyncIOMotorClient = Depends(get_database)):
    dbuser = await get_user(db, current_user.username)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    user_permissions = await 获取某用户的所有权限(db, dbuser)
    user_security_scopes = [":".join([key, value]).replace("*", ".*") for key in user_permissions.permissions for value in user_permissions.permissions[key]]
    token = create_access_token(data={"username": dbuser.username, "scopes": user_security_scopes}, expires_delta=access_token_expires)
    return dict(token=token)


@router.put("/subscribe/{sid}/equipments", description="订阅装备", response_model=ResultInResponse)
async def subscribe_equipment_action_view(
    sid: str = Path(..., regex=EQUIPMENT_SID_RE),
    is_subscribe: bool = Query(True, description="是否为订阅，不是订阅则是取消订阅"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    check_equipment_permission(sid, user)
    equipment = await 查询某个装备的详情(db, sid)
    if not equipment:
        raise NoEquipError
    equipment.作者 = equipment.作者.username
    if equipment.作者 == user.username:
        raise EquipCanNotBeSubscribed(message=f"无法订阅自己创建的装备")
    if is_subscribe and equipment.状态 != 装备状态.已上线:
        raise EquipCanNotBeSubscribed(message=f"该装备无法被订阅")
    if is_subscribe:
        result = await 订阅装备(db, user, equipment)
    else:
        result = await 取消订阅装备(db, user, equipment)
    return result


@router.put("/subscribe/{sid}/robots", description="订阅机器人", response_model=ResultInResponse)
async def subscribe_robot_action_view(
    sid: str = Path(..., regex="^10", min_length=14, max_length=14),
    is_subscribe: bool = Query(True, description="是否为订阅，不是订阅则是取消订阅"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    check_robot_permission(sid, user)
    robot = await 查询某机器人信息(db, sid, False, user)
    robot.作者 = robot.作者.username
    if robot.作者 == user.username:
        raise RobotCanNotBeSubscribed(message=f"无法订阅自己创建的机器人")
    if is_subscribe and robot.状态 != 机器人状态.已上线:
        raise RobotCanNotBeSubscribed(message=f"该机器人无法被订阅")
    if is_subscribe:
        result = await 订阅机器人(db, user, robot)
    else:
        result = await 取消订阅机器人(db, user, robot)
    return result


@router.put("/subscribe/{id}/portfolios", description="订阅/取消订阅组合", response_model=ResultInResponse)
async def subscribe_portfolio_action_view(
    id: PyObjectId = Path(...),
    is_subscribe: bool = Query(True, description="是否为订阅，不是订阅则是取消订阅"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    portfolio = await get_portfolio_by_id(db, id)
    if not portfolio:
        raise NoPortfolioError
    if portfolio.username == user.username:
        raise PortfolioCanNotBeSubscribed(message=f"无法订阅自己创建的组合")
    if is_subscribe and portfolio.status != 组合状态.running:
        raise PortfolioCanNotBeSubscribed(message=f"该组合无法被订阅")
    if is_subscribe:
        result = await subscribe_portfolio(db, user, portfolio)
    else:
        result = await unsubscribe_portfolio(db, user, portfolio)
    return result


@router.get("/subscribe/portfolio/{portfolio_id}/exist", description="是否订阅组合", response_model=StatusInResponse)
async def subscribe_portfolio_exist_get_view(
    portfolio_id: PyObjectId = Path(...),
    user=Security(get_current_user_authorizer()),
):
    result = False
    if portfolio_id in user.portfolio.subscribe_info.focus_list:
        result = True
    return StatusInResponse(status=result)


@router.post("/message", description="创建消息", response_model=ResultInResponse)
async def message_create_view(
    db: AsyncIOMotorClient = Depends(get_database),
    usermessage: UserMessageInCreate = Body(..., description="消息体"),
    user=Security(get_current_user_authorizer(), scopes=["消息:创建"]),
):
    return await 创建消息(db, user, usermessage)


# TODO query时List类型的参数中带特定类型（如枚举）的时候，api代码未处理导致无法正常显示
@router.get("/messages", description="获取用户消息列表", response_model=UserMessageListInResponse)
async def message_list_view(
    category: List[消息分类] = Query(None, description="消息分类"),
    is_read: bool = Query(None, description="true筛选已读，false筛选未读，不传则获取全部"),
    start_date: Union[date, datetime] = Query(..., description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    end_date: Union[date, datetime] = Query(..., description="ISO 8601日期格式的字符串, 如: 2008-09-15."),
    limit: int = Query(20, gt=0, description="限制返回的条数，不可传0"),
    skip: int = Query(0, ge=0),
    field_sort: str = Query("-created_at", description="排序，默认按创建时间倒序排序"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    start_date = start_date if isinstance(start_date, datetime) else datetime.combine(start_date, datetime.min.time())
    end_date = end_date if isinstance(end_date, datetime) else datetime.combine(end_date, datetime.max.time())
    db_query = {"username": user.username, "category": {"$in": category} if category else {"$ne": None}, "created_at": {"$gte": start_date, "$lte": end_date}}
    if is_read is not None:
        db_query["is_read"] = is_read
    field_sort = [[field_sort[1:], 数据库排序.倒序.value] if field_sort.startswith("-") else [field_sort, 数据库排序.正序.value]]
    return await 获取某用户消息列表(db, db_query, limit, skip, field_sort)


@router.put("/message", description="已读用户消息", response_model=ResultInResponse)
async def message_put_view(
    id: str = Query(None, description="消息id，默认不传全部已读"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer()),
):
    return await read_user_message(db, id, user)


@router.put("/verify/vcode", description="验证vip邀请码", response_model=ResultInResponse)
async def verify_vip_code_action_view(
    code: str = Query(..., description="邀请码"), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer())
):
    """
    验证vip邀请码
    """
    if not code == settings.vip_code:
        raise VIPCodeError
    if user.roles != ["免费用户"]:
        raise UpgradeVIPError
    return await update_user_roles(db, user.id, ["VIP用户"])


@router.get("/portfolio_targets", response_model=List[UserPortfolioTargetInResponse], description="获取用户组合指标配置列表")
async def portfolio_targets_get_view(
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["用户:查看"]),
):
    return await get_user_portfolio_targets(db, user)


@router.post("/manufacturer", response_model=User, status_code=HTTP_201_CREATED)
async def manufacturer_create_view(
    user: ManufacturerUserInCreate = Body(..., embed=True), super_user=Security(get_current_user_authorizer()), db: AsyncIOMotorClient = Depends(get_database)
):
    if "超级用户" not in super_user.roles:
        raise PermissionDenied
    await check_free_user(db, mobile=user.mobile)
    async with await db.start_session() as s:
        async with s.start_transaction():
            return await create_manufacturer_user(db, user)


@router.get("/manufacturer", response_model=List[UserInResponse], description="厂商用户列表")
async def manufacturer_user_get_view(
    username: str = Query(None, description="用户名"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["用户:查看"]),
):
    if "超级用户" not in user.roles:
        raise PermissionDenied
    return await get_manufacturer_user(db, username)


@router.put("/manufacturer/{username}", response_model=UserInResponse, description="厂商用户更新")
async def manufacturer_user_update_view(
    username: str = Path(..., description="用户名"),
    data: KeyValueInResponse = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    current_user=Security(get_current_user_authorizer(), scopes=["用户:查看"]),
):
    if "超级用户" not in current_user.roles:
        raise PermissionDenied
    return await update_manufacturer_user(db, username, data)


@router.delete("/manufacturer/{username}", response_model=ResultInResponse, description="厂商用户删除")
async def manufacturer_user_delete_view(
    username: str = Path(..., description="用户名"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["用户:查看"]),
):
    if "超级用户" not in user.roles:
        raise PermissionDenied
    if await check_strategy_exist(db, username):
        raise PermissionDenied(message="存在已创建的装备或者机器人，不允许删除该用户")
    await delete_manufacturer_user(db, username)
    return ResultInResponse()


@router.get("/{category}/quota/check", response_model=ResultInResponse, description="是否允许创建某类型的产品")
async def check_create_quota_view(
    category: 产品分类 = Path(..., description="分类"),
    装备分类: 装备分类_3 = Query(None, description="装备分类"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["用户:查看"]),
):
    await 创建数量限制(db, category, user, 装备分类=装备分类)
    return ResultInResponse()
