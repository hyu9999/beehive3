from enum import unique, Enum


@unique
class 上传类型(str, Enum):
    avatar = "avatar"
    profile_background = "profile_background"
    card_background = "card_background"
    custom_emoji = "custom_emoji"
    composer = "composer"


@unique
class 社区文章动作(str, Enum):
    like = "like"
    unlike = "unlike"
    bookmark = "bookmark"
    remove_bookmark = "remove_bookmark"
