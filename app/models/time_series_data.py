from app.models.base.time_series_data import PositionTimeSeriesData, FundTimeSeriesData, \
    PortfolioAssessmentTimeSeriesData
from app.models.dbmodel import DBModelMixin


class PositionTimeSeriesDataInDB(DBModelMixin, PositionTimeSeriesData):
    """持仓时点数据."""


class FundTimeSeriesDataInDB(DBModelMixin, FundTimeSeriesData):
    """资产时点数据."""


class PortfolioAssessmentTimeSeriesDataInDB(DBModelMixin, PortfolioAssessmentTimeSeriesData):
    """组合评估时点数据."""
