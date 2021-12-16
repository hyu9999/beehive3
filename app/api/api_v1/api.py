from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    authentication,
    user,
    equipment,
    robot,
    strawman_data,
    object_action,
    permission,
    role,
    common,
    backtest,
    stock,
    tag,
    adam,
    operation,
    activity,
    msg,
    log,
    portfolio,
    target_config,
    order,
    solution,
    signal,
    user_data,
    publish,
    zvt_data_log,
    fund_account,
    strategy_data,
)
from app.api.api_v1.endpoints import dashboard
from app.api.api_v1.endpoints import disc
from app.api.api_v1.endpoints import task

router = APIRouter()
router.include_router(authentication.router, prefix="/auth", tags=["身份认证"])
router.include_router(user.router, prefix="/user", tags=["用户"])
router.include_router(user_data.router, prefix="/user_data", tags=["用户数据"])
router.include_router(equipment.router, prefix="/equipment", tags=["装备"])
router.include_router(robot.router, prefix="/robots", tags=["机器人"])
router.include_router(backtest.router, prefix="/backtest", tags=["回测"])
router.include_router(strawman_data.router, prefix="/strawman_data", tags=["稻草人数据"])
router.include_router(object_action.router, prefix="/object_actions", tags=["对象和操作"])
router.include_router(permission.router, prefix="/permissions", tags=["权限"])
router.include_router(role.router, prefix="/roles", tags=["角色"])
router.include_router(common.router, prefix="/common", tags=["公共包"])
router.include_router(stock.router, prefix="/stock", tags=["股票"])
router.include_router(tag.router, prefix="/tag", tags=["标签"])
router.include_router(adam.router, prefix="/adam", tags=["adam"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(disc.router, prefix="/disc", tags=["社区"])
router.include_router(operation.router, prefix="/operation", tags=["运营数据"])
router.include_router(activity.router, prefix="/activity", tags=["活动相关"])
router.include_router(msg.router, prefix="/message", tags=["消息配置"])
router.include_router(log.router, prefix="/log", tags=["日志"])
router.include_router(portfolio.router, prefix="/portfolio", tags=["组合"])
router.include_router(order.router, prefix="/orders", tags=["订单"])
router.include_router(target_config.router, prefix="/target_config", tags=["指标配置"])
router.include_router(solution.router, prefix="/solutions", tags=["解决方案"])
router.include_router(signal.router, prefix="/signal", tags=["信号"])
router.include_router(task.router, prefix="/task", tags=["后台任务"])
router.include_router(publish.router, prefix="/publish", tags=["发布日志"])
router.include_router(zvt_data_log.router, prefix="/zvt_data_log", tags=["zvt数据日志"])
router.include_router(fund_account.router, prefix="/fund_account", tags=["资金账户"])
router.include_router(strategy_data.router, prefix="/strategy_data", tags=["策略数据"])
