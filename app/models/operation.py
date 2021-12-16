from app.models.base.operation import 趋势图信息
from app.models.dbmodel import DBModelMixin


class TrendChart(DBModelMixin, 趋势图信息):
    """趋势图表"""
