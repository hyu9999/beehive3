from typing import List

from fastapi import APIRouter, Depends, Security, Body
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.jwt import get_current_user_authorizer
from app.crud.portfolio import get_portfolio_by_id
from app.db.mongodb import get_database
from app.enums.solution import SolutionTypeEnum, SolutionStepEnum
from app.models.rwmodel import PyObjectId
from app.schema.order import SolutionOrderItem
from app.schema.solution import GetSolutionInResponse
from app.service.solutions.solution import Solution

router = APIRouter()


@router.post("", response_model=GetSolutionInResponse, description="根据确认的风险点生成解决方案")
async def get_solution_view(
    portfolio_id: PyObjectId = Body(..., embed=True, description="组合ID"),
    solutions_steps: List[SolutionStepEnum] = Body(None, embed=True, description="解决方案历史步骤"),
    solutions_types: List[SolutionTypeEnum] = Body(None, embed=True, description="当前已经发生过的解决步骤状态"),
    modified_orders: List[SolutionOrderItem] = Body([], embed=True, description="修改过的委托订单"),
    db: AsyncIOMotorClient = Depends(get_database),
    user=Security(get_current_user_authorizer(), scopes=["组合:修改"]),
):
    """根据组合已确认的风险点生成解决方案"""
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    return await Solution.generate(db, portfolio, solutions_steps, solutions_types, modified_orders)
