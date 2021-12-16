from app.models.base.publish import StrategyDailyLog, StrategyPublishLog
from app.models.dbmodel import DBModelMixin


class StrategyDailyLogInDB(DBModelMixin, StrategyDailyLog):
    """策略每日日志."""


class StrategyPublishLogInDB(DBModelMixin, StrategyPublishLog):
    """策略发布日志."""
