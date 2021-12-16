from datetime import datetime
from typing import Optional, List, Union

from pydantic import EmailStr, Field

from app.enums.user import 用户状态, 账户状态, 消息类型, 发送消息类型, 消息分类, 用户分类
from app.models import MOBILE_RE
from app.models.base.target_config import 指标配置基本信息
from app.models.rwmodel import EmbeddedDocument, RWModel, PyObjectId


class 账户信息(EmbeddedDocument):
    status: 账户状态 = Field(0, title="账户状态")
    is_tried: bool = Field(False, title="是否试用过")
    expired_at: datetime = Field(default_factory=datetime.utcnow, title="过期时间")


class 指标配置(EmbeddedDocument):
    trade_stats: List[指标配置基本信息] = Field([], title="交易统计配置")
    stock_stats: List[指标配置基本信息] = Field([], title="个股统计配置")
    portfolio_target: List[指标配置基本信息] = Field([], title="组合指标配置")


class 订阅信息(EmbeddedDocument):
    fans_num: int = Field(0, title="粉丝数")
    focus_num: int = Field(0, title="关注数")
    focus_list: List = Field([], title="关注列表")


class 创建信息(EmbeddedDocument):
    create_num: int = Field(0, title="创建数量")
    running_list: List[Union[PyObjectId, str]] = Field([], title="运行产品列表")
    closed_list: List[Union[PyObjectId, str]] = Field([], title="关闭产品列表")


class 订阅和创建信息(EmbeddedDocument):
    subscribe_info: 订阅信息 = Field(订阅信息(), title="订阅信息")
    create_info: 创建信息 = Field(创建信息(), title="创建信息")
    msg_num: int = Field(0, title="消息数")


class 用户基本信息(RWModel):
    username: str = Field(..., title="用户名")
    status: 用户状态 = Field(..., title="状态")
    nickname: str = Field(None, title="昵称")
    email: EmailStr = Field(None, title="邮箱")
    introduction: str = Field("", title="介绍")
    avatar: str = Field(None, title="头像")
    roles: Optional[List[str]] = Field(None, title="角色")
    mobile: str = Field(None, title="手机", regex=MOBILE_RE)
    equipment: 订阅和创建信息 = Field(订阅和创建信息(), title="装备信息")
    robot: 订阅和创建信息 = Field(订阅和创建信息(), title="机器人信息")
    portfolio: 订阅和创建信息 = Field(订阅和创建信息(), title="组合信息")
    account: 账户信息 = Field(账户信息(), title="账户信息")
    target_config: 指标配置 = Field(指标配置(), title="指标配置")
    open_id: str = Field(None, title="微信open_id")
    union_id: str = Field(None, title="微信union_id")
    send_flag: bool = Field(True, title="发送消息开关")
    send_type: 发送消息类型 = Field(None, title="发送消息类型")
    disc_id: int = Field(None, title="社区用户id")
    used_cell_num: int = Field(None, title="已使用计算单元数")
    category: 用户分类 = Field(用户分类.小白, title="用户分类")


class 用户消息基本信息(RWModel):
    title: str = Field(..., title="标题")
    content: str = Field(..., title="内容")
    category: 消息分类 = Field(..., title="消息分类")
    msg_type: 消息类型 = Field(..., title="消息类型")
    username: str = Field(..., title="用户名")
    data_info: str = Field(None, title="基本信息")
    is_read: bool = Field(False, title="是否已读")


class 厂商基本信息(RWModel):
    robot: List = Field([], title="机器人")
    equipment: List = Field([], title="装备")
    indicator: List = Field([], title="指示信号")
    base_url: str = Field(None, title="网站地址")
    expired_at: datetime = Field(None, title="过期时间")
    sync_date: datetime = Field(None, title="同步数据日期")
    can_create_robot: bool = Field(False, title="是否可创建机器人")
    can_create_equipment: bool = Field(False, title="是否可创建装备")
    can_sync_strategy_data: bool = Field(False, title="是否可以同步策略数据")
