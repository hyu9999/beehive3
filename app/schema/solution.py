from typing import List

from pydantic import Field

from app.enums.solution import SolutionStepEnum, SolutionTypeEnum
from app.models.rwmodel import RWModel
from app.schema.order import SolutionOrderItem


class SolutionItem(RWModel):
    """
    组成解决方案的最小元素
    """

    solution_type: SolutionTypeEnum = Field(..., description="解决方案元素类型")
    orders: List[SolutionOrderItem] = Field(..., description="装备给出的解决方案订单")


class GetSolutionInResponse(RWModel):
    title: str = Field(..., description="当前解决方案的步骤名")
    solutions: List[SolutionItem] = Field(..., description="针对同一目标的方案列表")
    aims: List[str] = Field(..., description="解决方案要解决的目标列表")
    step: SolutionStepEnum = Field(..., description="解决方案当前步骤状态")
    status: str = Field(..., description="按照当前解决方案交易后的状态")
    final_position: float = Field(None, description="预计仓位")
    recommend_position: List[float] = Field(None, description="建议仓位")
