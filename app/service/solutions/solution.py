from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from stralib import Robot

from app.core.errors import HasResolvingRisk
from app.enums.solution import SolutionTypeEnum, SolutionStepEnum
from app.models.portfolio import Portfolio
from app.schema.order import SolutionOrderItem
from app.schema.solution import GetSolutionInResponse
from app.service.fund_account.fund_account import get_fund_asset, get_fund_account_position
from app.service.risks.risk import get_position_risks_step
from app.service.solutions.ret_msg import fmt_rsp_msg
from app.service.solutions.solution_list import get_non_position_solutions, get_position_solutions, \
    get_confirm_buy_new_stock_solutions, get_final_solutions
from app.service.solutions.utils import get_robot


class Solution:
    """
    生成解决方案
    Parameters
    ----------
    last_step_solutions 上一步传入的解决方案
    solutions_steps     解决方案历史步骤
    solutions_types     解决方案类型
    portfolio           PortfolioInResponse

    Returns
    -------
        GetSolutionInResponse
    """

    @classmethod
    async def generate(
        cls,
        conn: AsyncIOMotorClient,
        portfolio: Portfolio,
        solutions_steps: List[SolutionStepEnum],
        solutions_types: List[SolutionTypeEnum],
        last_step_solutions: List[SolutionOrderItem],
    ) -> GetSolutionInResponse:
        """生成解决方法"""
        # 根据用户组合所属账户最近的持仓数据与组合信息和挂单列表构造robot对象
        fund_account = portfolio.fund_account[0]
        fund_asset = await get_fund_asset(conn, fund_account.fundid, portfolio.category, fund_account.currency)
        position_list = await get_fund_account_position(conn, fund_account.fundid, portfolio.category)
        robot = await get_robot(portfolio, fund_asset, position_list, last_step_solutions)
        # 根据组合内的风险点确认当前解决步骤
        current_step = await cls.confirm_risks(portfolio, solutions_steps, solutions_types, robot)
        # 已全部解决
        if current_step == SolutionStepEnum.END_FLAG and (not last_step_solutions):
            solution = await fmt_rsp_msg(SolutionStepEnum.END_FLAG)
            return GetSolutionInResponse(**solution)
        # 止盈止损、调仓周期、个股风险解决方案
        elif current_step == SolutionStepEnum.STOPLOSSTAKEPROFIT_CHANGEPOSITION_INDIVIDUALSTOCK:
            return await get_non_position_solutions(portfolio, robot, position_list)
        # 仓位风险解决方案
        elif current_step in [SolutionStepEnum.UNDERWEIGHT, SolutionStepEnum.OVERWEIGHT]:
            return await get_position_solutions(robot, position_list)
        # 确认买入新股票解决方案
        elif current_step == SolutionStepEnum.NEW_STOCK:
            return await get_confirm_buy_new_stock_solutions(robot, last_step_solutions)
        # 最终解决方案
        else:
            return await get_final_solutions(robot, fund_asset, position_list, last_step_solutions)

    @staticmethod
    async def confirm_risks(
        portfolio: Portfolio, solutions_steps: List[SolutionStepEnum], solutions_types: List[SolutionTypeEnum], robot: Robot,
    ) -> SolutionStepEnum:
        """确认风险"""
        # 若存在解决中的风险点则跳过
        if portfolio.has_solving_risks():
            raise HasResolvingRisk
        if solutions_steps:
            last_step = solutions_steps[-1]
        else:
            last_step = SolutionStepEnum.START_FLAG
        # 1. 检查是否有止盈止损、调仓周期、个股风险
        stocks_risks = portfolio.get_confirmed_non_position_risks()
        if stocks_risks:
            current_step = SolutionStepEnum.STOPLOSSTAKEPROFIT_CHANGEPOSITION_INDIVIDUALSTOCK
            if last_step.value < current_step.value:
                return current_step
        # 2. 检查是否有仓位风险
        step = await get_position_risks_step(portfolio, robot)
        if step and last_step.value < SolutionStepEnum.UNDERWEIGHT.value:
            current_step = step
            if last_step.value < current_step.value:
                return current_step
        # 3. 确认买入新股票（只有上一步是仓位过轻，才会触发）
        solutions_type = solutions_types[-1]
        if last_step == SolutionStepEnum.UNDERWEIGHT and solutions_type == SolutionTypeEnum.NEW_STOCKS:
            current_step = SolutionStepEnum.NEW_STOCK
            return current_step

        current_step = SolutionStepEnum.END_FLAG
        return current_step
