from app.models.base.object_action import 对象行为基本信息


class ObjectAction(对象行为基本信息):
    """对象行为表（虚拟表）"""


################################################
# 对象及其可能的操作
# 注意操作遵循一个原则，即如果没有标注他人的操作则表示是操作自己的对象，只有明确标注了他人字样的操作才是操作他人的对象的操作，如修改他人。
################################################
组合 = ObjectAction(url_prefix="/portfolio", name="组合", actions=["创建", "修改", "查看", "订阅", "取消订阅"])
装备 = ObjectAction(url_prefix="/equipment", name="装备", actions=["创建", "修改", "查看", "订阅", "取消订阅", "修改他人", "删除他人"])
机器人 = ObjectAction(url_prefix="/robots", name="机器人", actions=["创建", "修改", "查看", "订阅", "取消订阅", "修改他人", "删除他人"])
文章 = ObjectAction(url_prefix="/articles", name="文章", actions=["创建", "修改", "查看"])
赞 = ObjectAction(url_prefix="/like", name="赞", actions=["创建", "修改", "查看"])
评论 = ObjectAction(url_prefix="/comments", name="评论", actions=["创建", "修改", "查看"])
活动 = ObjectAction(url_prefix="/works", name="活动", actions=["创建", "修改", "查看"])
用户 = ObjectAction(url_prefix="/users", name="用户", actions=["创建", "修改", "查看"])
稻草人数据 = ObjectAction(url_prefix="/strawman_data", name="稻草人数据", actions=["创建", "修改", "查看"])
对象和操作 = ObjectAction(url_prefix="/object_actions", name="对象和操作", actions=["查看"])
角色 = ObjectAction(url_prefix="/roles", name="角色", actions=["创建", "修改", "查看", "删除"])
权限 = ObjectAction(url_prefix="/permissions", name="权限", actions=["创建", "修改", "查看", "删除"])
厂商数据 = ObjectAction(url_prefix="/clients", name="厂商数据", actions=["创建", "修改", "查看", "删除"])
运营数据 = ObjectAction(url_prefix="/operations", name="运营数据", actions=["查看"])
日志 = ObjectAction(url_prefix="/logs", name="日志", actions=["创建", "修改", "查看", "删除"])
自选股 = ObjectAction(url_prefix="/favorite_stock", name="自选股", actions=["创建", "修改", "查看", "删除"])
指标配置 = ObjectAction(url_prefix="/target_config", name="指标配置", actions=["创建", "修改", "查看", "删除"])
标签 = ObjectAction(url_prefix="/tags", name="标签", actions=["创建", "删除", "查看", "修改"])
策略数据 = ObjectAction(url_prefix="/strategy_data", name="策略", actions=["创建", "删除", "查看", "修改"])
后台任务 = ObjectAction(url_prefix="/background_tasks", name="后台任务", actions=["创建", "删除", "查看", "修改", "执行"])
