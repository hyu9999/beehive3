from copy import deepcopy
from typing import Any, Dict, List

from hq2redis import HQSourceError, SecurityNotFoundError
from pydantic import ValidationError
from stralib import Robot

from app.crud.equipment import 查询某个装备的详情
from app.db.mongodb import db
from app.enums.log import 买卖方向
from app.enums.portfolio import 风险类型
from app.enums.robot import 减仓模式
from app.enums.solution import SolutionStepEnum, SolutionTypeEnum
from app.extentions import logger
from app.models.base.portfolio import 风险点信息
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.outer_sys.hq import get_security_info, get_security_hq
from app.outer_sys.stralib.robot.run_robot import database_stock_list_to_robot
from app.outer_sys.stralib.robot.utils import exchange_format, signal_to_api
from app.schema.order import SolutionOrderItem
from app.schema.solution import GetSolutionInResponse
from app.service.datetime import str_of_today
from app.service.equipment import format_trade_equipment_strategy_word
from app.service.risks.risk import get_sl_tp_risks
from app.service.risks.utils import select_stock_signals
from app.service.solutions.ret_msg import fmt_rsp_msg, market_from_symbol
from app.service.solutions.utils import (
    build_risk_set,
    build_signal_index,
    update_account_info,
)


async def get_sl_tp_solutions(
    user_accepted_risks: List[风险点信息], position_list: List[FundAccountPositionInDB]
) -> List[Dict[str, Any]]:
    """止盈止损风险解决方案"""
    all_solutions = []
    stocks = await database_stock_list_to_robot(position_list)
    for user_accepted_risk in user_accepted_risks:
        try:
            quantity = [
                x["stkbal"] for x in stocks if x["symbol"] == user_accepted_risk.symbol
            ][0]
        except Exception as e:
            logger.warning(f"获取股票数量失败{e}")
        else:
            stock_dict = {
                "exchange": user_accepted_risk.exchange,
                "symbol": user_accepted_risk.symbol,
                "operator": 买卖方向.sell,
                "quantity": quantity,
                "price": -1,
                "reason": "0",  # 解决止盈止损股票持仓的标志
                "date": str_of_today(),
            }
            all_solutions.append(stock_dict)
    return all_solutions


async def get_stock_solutions(
    robot: Robot, accepted_risks: List[风险点信息]
) -> List[Dict[str, Any]]:
    """个股风险解决方案"""
    robot.get_hold_risk()
    accepted_risk_set = await build_risk_set(accepted_risks)
    stock_signal_list = await select_stock_signals(robot.all_risk_list)
    all_solutions = []
    for signal in stock_signal_list:
        index = await build_signal_index(signal)
        if index and index in accepted_risk_set:
            accepted_risk_set.remove(index)
            signal["TDATE"] = (
                signal["TDATE"]
                if isinstance(signal["TDATE"], str)
                else signal["TDATE"].strftime("%Y%m%d")
            )
            await signal_to_api(signal)
            all_solutions.append(signal)
    return all_solutions


async def get_non_position_solutions(
    portfolio: Portfolio,
    robot: Robot,
    position_list: List[FundAccountPositionInDB],
) -> GetSolutionInResponse:
    """获取止盈止损、调仓周期、个股风险解决方案"""
    # 止盈止损风险解决方案, 生成订单
    sl_tp_risks = await get_sl_tp_risks(portfolio)
    sl_tp_solutions = await get_sl_tp_solutions(sl_tp_risks, position_list)
    # 获取组合的风险
    accepted_risks = portfolio.get_confirmed_risks()
    # 调仓风险解决方案
    change_position_risks = [
        risk for risk in accepted_risks if risk.risk_type == 风险类型.adjustment_cycle
    ]
    change_position_solution = await get_sl_tp_solutions(
        change_position_risks, position_list
    )
    # 个股风险解决
    stock_risks = [
        risk for risk in accepted_risks if risk.risk_type != 风险类型.adjustment_cycle
    ]
    stock_solutions = await get_stock_solutions(robot, stock_risks)
    all_solutions = []
    if sl_tp_solutions:
        logger.debug(f"sl_tp_solutions:{sl_tp_solutions}")
        all_solutions.extend(sl_tp_solutions)
    if stock_solutions:
        logger.debug(f"stock_solutions:{stock_solutions}")
        all_solutions.extend(stock_solutions)
    if change_position_solution:
        logger.debug(f"change_position_solution:{change_position_solution}")
        all_solutions.extend(change_position_solution)
    symbol_list = []
    new_orders = []
    # 剔除同一个股触发多条风险导致的多次卖出的解决方案和交易数量为0的订单
    for order_dict in all_solutions:
        if order_dict["symbol"] not in symbol_list and order_dict.get("quantity"):
            symbol_list.append(order_dict["symbol"])
            new_orders.append(order_dict)
    all_solutions = new_orders
    [x.pop("status", None) for x in all_solutions]
    # 构造返回数据
    robot.check_position()
    final_position = robot.current_position
    recommend_position = robot.timing_signal
    recommend_list = [float(x) / 100 for x in recommend_position[:-1].split("-")]
    position_info = {
        "final_position": final_position,
        "recommend_position": recommend_list,
    }
    solutions = [{"orders": all_solutions, "solution_type": SolutionTypeEnum.SIMPLE}]
    description = "个股风险需要全部卖出, 必须狠下心来, 斩草要除根"
    solution = await fmt_rsp_msg(
        SolutionStepEnum.STOPLOSSTAKEPROFIT_CHANGEPOSITION_INDIVIDUALSTOCK,
        solutions,
        description,
        **position_info,
    )
    return GetSolutionInResponse(**solution)


async def get_scale_up_solutions(robot: Robot) -> Dict[str, Any]:
    """同比例加仓解决方案"""
    robot.tb_add_position()
    solution_type = SolutionTypeEnum.SCALE_UP
    result_orders = [
        await signal_to_api(signal)
        for signal in robot.add_programme
        if signal.get("STKEFFEFT")
    ]
    final_position = robot.final_position
    description = (
        f"此方案成交后预计仓位为 {round(final_position * 100, 2)}%，推荐仓位为 {robot.timing_signal}"
    )
    solution = dict(
        solution_type=solution_type, orders=result_orders, description=description
    )
    return solution


async def get_new_stock_solutions(robot: Robot) -> Dict[str, Any]:
    """买入新股票方案"""
    solution_type = SolutionTypeEnum.NEW_STOCKS
    result_orders = []
    # 生成推荐的股票
    robot.get_recommend_stocks()
    for symbol, value in robot.recommend_stocks_dict.items():
        exchange = market_from_symbol(symbol)
        opinion_id = value[2]
        opinion = ""
        if str(value[0]) == "3":  # 交易装备
            equipment = await 查询某个装备的详情(db.client, opinion_id)
            if equipment:
                opinion = format_trade_equipment_strategy_word(
                    "('买1',)", equipment.策略话术
                )
        else:  # 选股装备
            equipment = await 查询某个装备的详情(db.client, opinion_id)
            if equipment:
                opinion = equipment.策略话术
        try:
            security = await get_security_info(symbol, exchange)
        except (ValidationError, HQSourceError, SecurityNotFoundError):
            continue
        else:
            stock_dict = dict(
                exchange=exchange,
                symbol=symbol,
                operator=买卖方向.buy,
                quantity=0,
                name=value[1],
                price=-1,
                reason="12",  # 买入新股票的标志
                date=str_of_today(),
                opinion=opinion,  # 买入新股票的入选理由
                symbol_name=security.symbol_name,
            )
            result_orders.append(stock_dict)
    final_position = robot.final_position
    description = (
        f"此方案成交后预计仓位为 {round(final_position * 100, 2)}%，推荐仓位为 {robot.timing_signal}"
    )
    solution = dict(
        solution_type=solution_type, orders=result_orders, description=description
    )
    return solution


async def get_light_position_solutions(robot: Robot) -> List[Dict[str, Any]]:
    """获取仓位过轻解决方案"""
    solutions = []
    # 同比例加仓
    scale_up_solutions = await get_scale_up_solutions(robot)
    solutions.append(scale_up_solutions)
    # 买入新股票
    new_stock_solutions = await get_new_stock_solutions(robot)
    solutions.append(new_stock_solutions)
    return solutions


async def get_scale_down_solution(robot: Robot) -> Dict[str, Any]:
    """同比例减仓解决方案"""
    solution_type = SolutionTypeEnum.SCALE_DOWN
    orders = [
        await signal_to_api(x) for x in robot.reduce_programme if x.get("STKEFFEFT")
    ]
    solution = dict(solution_type=solution_type, orders=orders)
    return solution


async def get_roguing_solution(robot: Robot) -> Dict[str, Any]:
    """去弱留强解决方案"""
    roguing_robot = deepcopy(robot)
    roguing_robot._rconfig.reduce = 减仓模式.去弱留强.value
    roguing_robot.check_position()
    roguing_robot.reduce_position()
    orders = [
        await signal_to_api(x)
        for x in roguing_robot.reduce_programme
        if x.get("STKEFFEFT")
    ]
    solution = dict(solution_type=SolutionTypeEnum.ROGUING, orders=orders)
    return solution


async def get_customize_solution(
    position_list: List[FundAccountPositionInDB],
) -> Dict[str, Any]:
    """自定义解决方案"""
    orders = []
    for position in position_list:
        if position.volume:
            order = position.dict(include={"symbol", "exchange"})
            try:
                security = await get_security_hq(
                    symbol=position.symbol,
                    exchange=market_from_symbol(position.symbol)
                )
            except (ValidationError, HQSourceError, SecurityNotFoundError):
                continue
            else:
                order.update({
                    "symbol_name": security.symbol_name,
                    "quantity": position.volume,
                    "operator": 买卖方向.sell,
                    "price": security.current,
                    "reason": "11",
                    "date": str_of_today()
                })
                exchange_format(order)
                orders.append(order)
    solution = dict(solution_type=SolutionTypeEnum.CUSTOMIZE, orders=orders)
    return solution


async def get_weight_position_solutions(
    robot: Robot, position_list: List[FundAccountPositionInDB]
) -> List[Dict[str, Any]]:
    """仓位过重解决方案"""
    robot.reduce_position()
    solutions = []
    # 同比例减仓
    scale_down_solutions = await get_scale_down_solution(robot)
    solutions.append(scale_down_solutions)
    # 去弱留强
    roguing_solutions = await get_roguing_solution(robot)
    solutions.append(roguing_solutions)
    # 自定义
    customize_solution = await get_customize_solution(position_list)
    solutions.append(customize_solution)
    return solutions


async def get_position_solutions(
    robot: Robot,
    position_list: List[FundAccountPositionInDB],
) -> GetSolutionInResponse:
    """仓位风险解决方案"""
    solutions = []
    robot.check_position()
    suggested_positions_range = [
        float(robot.timing_signal.split("-")[0]) / 100,
        float(robot.timing_signal.split("-")[1][:-1]) / 100,
    ]
    position_status = SolutionStepEnum.START_FLAG
    final_position = 0
    # 仓位过轻
    if robot.current_position < suggested_positions_range[0]:
        position_status = SolutionStepEnum.UNDERWEIGHT
        solutions = await get_light_position_solutions(robot)
        final_position = robot.final_position
    # 仓位过重
    elif robot.current_position > suggested_positions_range[1]:
        position_status = SolutionStepEnum.OVERWEIGHT
        solutions = await get_weight_position_solutions(robot, position_list)
        final_position = robot.reduce_final_position
    # 构造返回数据
    recommend_position = robot.timing_signal
    recommend_list = [float(x) / 100 for x in recommend_position[:-1].split("-")]
    position_info = {
        "final_position": final_position,
        "recommend_position": recommend_list,
    }
    description = (
        f"此方案成交后预计仓位为 {round(final_position * 100, 2)}%，推荐仓位为 {recommend_position}"
    )
    solution = await fmt_rsp_msg(
        position_status, solutions, description, **position_info
    )
    return GetSolutionInResponse(**solution)


async def get_confirm_buy_new_stock_solutions(
    robot: Robot, last_step_solutions: List[SolutionOrderItem]
) -> GetSolutionInResponse:
    """确认买入新股票解决方案"""
    # 过滤买卖方向保持不变的股票
    symbols = [s.symbol for s in last_step_solutions if s.operator != 买卖方向.unchanged]
    robot.get_buy_programme(symbols)
    result_orders = []
    for signal in robot.buy_programme:
        if signal.get("STKEFFEFT"):
            await signal_to_api(signal)
            signal["reason"] = "9"  # 将订单的买入原因改为仓位过轻对应的原因
            result_orders.append(signal)

    # 构造返回数据
    robot.check_position()
    final_position = robot.final_position
    recommend_position = robot.timing_signal
    recommend_list = [float(x) / 100 for x in recommend_position[:-1].split("-")]
    position_info = {
        "final_position": final_position,
        "recommend_position": recommend_list,
    }
    solutions = [{"orders": result_orders, "solution_type": SolutionTypeEnum.SIMPLE}]
    description = (
        f"此方案成交后预计仓位为 {round(final_position * 100, 2)}%，推荐仓位为 {recommend_position}"
    )
    solution = await fmt_rsp_msg(
        SolutionStepEnum.NEW_STOCK, solutions, description, **position_info
    )
    return GetSolutionInResponse(**solution)


async def get_final_solutions(
    robot: Robot,
    fund_asset: FundAccountInDB,
    position_list: List[FundAccountPositionInDB],
    last_step_solutions: List[SolutionOrderItem],
) -> GetSolutionInResponse:
    """最终解决方案"""
    # 过滤买入新股票的挂单，根据挂单重置robot中的_asset，_fundbal，_mktval数据
    last_step_solutions = [s for s in last_step_solutions if s.reason != "12"]
    _fundbal, _mktval = await update_account_info(
        last_step_solutions, fund_asset, position_list
    )
    robot._fundbal, robot._mktval = _fundbal.to_decimal(), _mktval.to_decimal()
    robot._asset = robot._fundbal + robot._mktval
    # 构造返回数据
    robot.check_position()
    final_position = robot.current_position
    recommend_position = robot.timing_signal
    recommend_list = [float(x) / 100 for x in recommend_position[:-1].split("-")]
    position_info = {
        "final_position": final_position,
        "recommend_position": recommend_list,
    }
    orders = [x for x in last_step_solutions if x.quantity]
    solutions = [{"orders": orders, "solution_type": SolutionTypeEnum.SIMPLE}]
    description = (
        f"此方案成交后预计仓位为 {round(final_position * 100, 2)}%，推荐仓位为 {recommend_position}"
    )
    # TODO: 机器人日志记录：根据优化点生成解决方案
    solution = await fmt_rsp_msg(
        SolutionStepEnum.END_FLAG, solutions, description, **position_info
    )
    return GetSolutionInResponse(**solution)
