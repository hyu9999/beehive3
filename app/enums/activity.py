from enum import Enum, unique


@unique
class 活动状态(str, Enum):
    pre_online = "pre_online"  # 预上线
    online = "online"  # 已上线
    offline = "offline"  # 已下线
    deleted = "deleted"  # 已删除
