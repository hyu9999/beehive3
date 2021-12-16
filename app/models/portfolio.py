from datetime import datetime
from typing import Optional

from pydantic import Field

from app.enums.portfolio import PortfolioCategory, 风险点状态, 风险类型
from app.models.base.portfolio import 总收益排行信息, 组合基本信息, 组合阶段收益, 统计数据信息
from app.models.dbmodel import DBModelMixin
from app.models.rwmodel import PyObjectId


class Portfolio(DBModelMixin, 组合基本信息, 总收益排行信息):
    """组合表"""

    stage_profit: 组合阶段收益 = Field(组合阶段收益(), title="统计数据")
    category: PortfolioCategory = Field(PortfolioCategory.SimulatedTrading, description="组合类型")
    activity: PyObjectId = Field(None, title="活动")
    create_date: datetime = Field(default_factory=datetime.utcnow, title="创建时间")
    close_date: datetime = Field(..., title="结束时间")
    update_account_data: bool = Field(False, title="是否需要更新时点数据")
    update_account_start_date: datetime = Field(None, title="需要更新的时点数据开始日期")
    import_date: Optional[datetime] = Field(None, title="最早导入持仓时间")

    def has_solving_risks(self):
        solving_list = [x for x in self.risks if x.status == 风险点状态.solving]
        return True if solving_list else False

    def get_ignore_risks(self):
        return [x for x in self.risks if x.status == 风险点状态.ignored]

    def get_confirmed_risks(self):
        return [x for x in self.risks if x.status == 风险点状态.confirmed]

    def get_confirmed_non_position_risks(self):
        return [x for x in self.risks if x.status == 风险点状态.confirmed and x.risk_type not in (风险类型.overweight, 风险类型.underweight)]

    def get_confirmed_position_risks(self):
        return [x for x in self.risks if x.status == 风险点状态.confirmed and x.risk_type in (风险类型.overweight, 风险类型.underweight)]


class PortfolioAnalysisInDB(DBModelMixin, 统计数据信息):
    """组合统计数据."""
