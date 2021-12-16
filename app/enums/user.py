from enum import unique, Enum


@unique
class 消息分类(str, Enum):
    portfolio = "portfolio"
    robot = "robot"
    equipment = "equipment"


@unique
class 消息类型(str, Enum):
    notice = "notice"  # 公告
    subscribe = "subscribe"  # 订阅
    online = "online"  # 上线
    offline = "offline"  # 下线
    review = "review"  # 审核
    signal = "signal"  # 信号
    risk = "risk"  # 风险
    comment = "comment"  # 评论
    task_finished = "task_finished"  # 任务执行成功
    sub_portfolio_closed = "sub_portfolio_closed"  # 订阅的组合被关闭
    order_generated = "order_generated"  # 委托订单生成
    portfolio_rank = "portfolio_rank"  # 组合排名


@unique
class 发送消息类型(str, Enum):
    email = "email"  # 邮箱
    we_chat = "we_chat"  # 微信
    not_send = "not_send"  # 不发送消息


@unique
class 用户状态(str, Enum):
    normal = "normal"  # 正常
    disable = "disable"  # 禁用
    log_off = "log_off"  # 注销
    first = "first"  # 首次


@unique
class 账户状态(int, Enum):
    unpaid = 0  # 未付费
    on_trial = 1  # 试用
    vip = 2  # 会员


@unique
class 用户分类(str, Enum):
    小白 = "1"
    半合格 = "2"
    合格 = "3"
    大师 = "4"
