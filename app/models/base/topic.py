from datetime import datetime
from typing import List

from pydantic import Field

from app.models.base.post import Action, UserMin, PostBase
from app.models.dbmodel import DateTimeModelMixin
from app.models.rwmodel import RWModel


class TopicBasic(RWModel):
    """主题基本信息"""

    id: int = Field(..., description="主题id")
    title: str = Field(..., description="标题")
    fancy_title: str = Field(None, description="高级标题")
    slug: str = Field(None, description="回复数")


class TopicExtra(DateTimeModelMixin, TopicBasic):
    """主题基扩展信息"""

    posts_count: int = Field(None, description="帖子数")
    reply_count: int = Field(None, description="回复数")
    highest_post_number: int = Field(None, description="回复数")
    image_url: str = Field(None, description="图片地址")
    last_posted_at: datetime = Field(None, description="最后回帖时间")
    bumped: bool = Field(None, description="重点关注")
    bumped_at: datetime = Field(None, description="重点关注时间")
    unseen: bool = Field(None, description="是否即席翻译")
    pinned: bool = Field(None, description="固定")
    unpinned: bool = Field(None, description="解除固定")
    excerpt: str = Field(None, description="节选")
    visible: bool = Field(None, description="是否可见")
    closed: bool = Field(None, description="是否关闭")
    archived: bool = Field(None, description="是否归档")
    bookmarked: bool = Field(None, description="是否被收藏")
    liked: bool = Field(None, description="是否点过赞")
    archetype: str = Field(None, description="典型")
    like_count: int = Field(None, description="点赞数")
    views: int = Field(None, description="查看数")
    category_id: int = Field(None, description="分类id")
    posters: List = Field(None, description="回帖人信息")


class Participant(UserMin):
    """参与者"""

    post_count: int = Field(None, description="回帖数")


class TopicDetails(RWModel):
    """详情"""

    auto_close_at: dict = Field(None, description="自动关闭情况")
    auto_close_hours: dict = Field(None, description="自动关闭时间")
    created_by: UserMin = Field(None, description="创建人信息")
    last_poster: UserMin = Field(None, description="会后回帖人")
    auto_close_based_on_last_post: bool = Field(None, description="自动关闭是否基于最后回复")
    participants: List[Participant] = Field(None, description="参与者列表")
    suggested_topics: List[TopicExtra] = Field(None, description="推荐主题列表")
    notification_level: int = Field(None, description="通知级别")
    can_flag_topic: bool = Field(None, description="是否可标记")


class PostStream(RWModel):
    """帖子信息"""

    posts: List[PostBase] = Field(None, description="帖子详情列表")
    stream: List[int] = Field(None, description="贴子id列表")


class TopicBase(TopicExtra):
    """主题"""

    timeline_lookup: List = Field(None, description="时间线")
    user_id: int = Field(None, description="用户id")
    participant_count: int = Field(None, description="参与者数量")
    has_summary: bool = Field(None, description="是否已经汇总")
    chunk_size: int = Field(None, description="快大小")
    actions_summary: List[Action] = Field(None, description="动作汇总")
    pinned_at: str = Field(None, description="固定信息")
    pinned_until: dict = Field(None, description="固定直到")
    pinned_globally: bool = Field(None, description="全球固定")
    word_count: int = Field(None, description="计数字数")
    deleted_by: UserMin = Field(None, description="删除人")
    deleted_at: datetime = Field(None, description="删除时间")
    draft: dict = Field(None, description="草稿")
    draft_key: str = Field(None, description="草稿密钥")
    draft_sequence: int = Field(None, description="草图顺序")
    post_stream: PostStream = Field(None, description="帖子列表")
