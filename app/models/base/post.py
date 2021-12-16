from datetime import datetime
from typing import List

from pydantic import Field

from app.models.dbmodel import DateTimeModelMixin
from app.models.rwmodel import RWModel

"""
社区：该模块为discourse内的帖子相关模型
"""


class UserMin(RWModel):
    """社区用户信息：min"""

    username: str = Field(None, description="账户")
    avatar_template: str = Field(None, description="用户头像")


class DUser(RWModel):
    """社区用户信息"""

    user_id: int = Field(None, description="用户id")
    name: str = Field(None, description="昵称")
    username: str = Field(None, description="账户")
    avatar_template: str = Field(None, description="用户头像")


class Action(RWModel):
    """动作"""

    id: int = Field(None, description="回复数")
    count: int = Field(None, description="回复数")
    hidden: bool = Field(None, description="回复数")
    can_act: bool = Field(None, description="回复数")


class PrimaryGroup(RWModel):
    """组信息"""

    primary_group_name: str = Field(None, description="组名")
    primary_group_flair_url: str = Field(None, description="组url")
    primary_group_flair_bg_color: str = Field(None, description="组背景色")
    primary_group_flair_color: str = Field(None, description="组颜色")


class PostPermission(RWModel):
    """权限"""

    can_edit: bool = Field(False, description="是否可以编辑")
    can_delete: bool = Field(False, description="是否可以删除")
    can_recover: bool = Field(False, description="是否可以覆盖")
    can_wiki: bool = Field(False, description="是否可以wiki")
    can_view_edit_history: bool = Field(False, description="是否可以wiki")
    admin: bool = Field(False, description="是否是管理员")
    staff: bool = Field(False, description="是否是员工")
    yours: bool = Field(0, description="是否是本人的")
    read: bool = Field(False, description="是否已经阅读过？")
    wiki: bool = Field(False, description="是否已经wiki")
    hidden: bool = Field(False, description="是否隐藏")
    moderator: bool = Field(False, description="仲裁人？")
    user_deleted: bool = Field(False, description="是否被用户删除")
    deleted_at: datetime = Field(None, description="删除时间")
    deleted_by: UserMin = Field(None, description="删除人")
    edit_reason: str = Field(None, description="编辑原因")


class Statistics(RWModel):
    """统计"""

    post_number: int = Field(0, description="回帖数？")
    post_type: int = Field(0, description="帖子类型")
    reply_count: int = Field(0, description="回复数")
    reply_to_post_number: int = Field(None, description="回复帖子数？")
    quote_count: int = Field(0, description="引用数？")
    incoming_link_count: int = Field(0, description="传入链接数？")
    reads: int = Field(0, description="阅读数")
    readers_count: int = Field(0, description="阅读人数")
    score: float = Field(0, description="分数")


class PostBase(DateTimeModelMixin, DUser, PostPermission, PrimaryGroup, Statistics):
    """帖子"""

    id: int = Field(None, description="帖子id")
    display_username: str = Field(None, description="展示的账户名?")
    cooked: str = Field(None, description="发帖内容")
    topic_id: int = Field(None, description="主题id")
    topic_slug: str = Field(None, description="主题词?")
    version: int = Field(None, description="版本")
    trust_level: int = Field(None, description="信任度")
    actions_summary: List = Field(False, description="动作汇总")
    user_title: str = Field(None, description="用户标题?")
    reply_to_user: UserMin = Field(None, description="回复人信息")
