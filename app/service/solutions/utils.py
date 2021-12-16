from copy import deepcopy
from decimal import Decimal
from typing import List, Dict, Any

from bson import Decimal128
from stralib import Robot

from app.enums.log import 买卖方向
from app.enums.portfolio import 风险类型
from app.models.base.portfolio import 风险点信息
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.outer_sys.stralib.robot.run_robot import account_robot_factory, database_stock_list_to_robot
from app.schema.order import SolutionOrderItem
from app.service.risks.utils import risk_type_from_signal, get_exchange_from_signal


async def build_signal_index(signal: Dict[str, Any]):
    """根据信号组建风险数据"""
    risk_type = risk_type_from_signal(signal)
    if risk_type in ("0", "1", "2", "3", "4", "5", "6", "7", "10", "12"):
        exchange = await get_exchange_from_signal(signal)
        item = (risk_type, signal["SYMBOL"], exchange)
    else:
        return None
    return item


async def build_risk_set(risks: List[风险点信息]):
    result = set()
    for risk in risks:
        if risk.risk_type in [风险类型.overweight, 风险类型.underweight]:
            item = (risk.risk_type,)
        elif risk.risk_type.value in ("0", "1", "2", "3", "4", "5", "6", "7", "10", "12"):
            item = (risk.risk_type, risk.symbol, risk.exchange)
        else:
            raise RuntimeError(f"风险点类型未知: {risk.risk_type}")
        result.add(item)
    return result


async def update_account_info(
    last_step_solutions: List[SolutionOrderItem],
    fund_asset: FundAccountInDB,
    position_list: List[FundAccountPositionInDB],
) -> (Decimal128, Decimal128):
    """根据上一步的解决方案刷新账户资金信息"""
    fund_bal, market_value = fund_asset.cash, fund_asset.securities
    for order in last_step_solutions:
        if order.operator == 买卖方向.sell:
            position_stock = list(filter(lambda x: x.symbol == order.symbol, position_list))
            if len(position_stock) == 0:
                continue
            p_stock = position_stock[0]
            if order.price != -1:
                fund_bal += Decimal(order.quantity * order.price)
            else:
                fund_bal += order.quantity * p_stock.cost.to_decimal()
            market_value -= p_stock.cost.to_decimal() * order.quantity
            if p_stock.volume == order.quantity:
                position_list.remove(p_stock)
            elif p_stock.volume > order.quantity:
                p_stock.volume -= order.quantity
            else:
                raise RuntimeError("卖出的股票数量超出了持有的数量")
        else:
            position_stock = list(filter(lambda x: x.symbol == order.symbol, position_list))
            if position_stock:
                position_stock[0].volume += order.quantity
                position_stock[0].cost = order.price
            cost = order.quantity * order.price
            fund_bal = Decimal128(str(fund_bal.to_decimal() - Decimal.from_float(cost)))
            market_value = Decimal128(str(market_value.to_decimal() + Decimal.from_float(cost)))
    return fund_bal, market_value


async def get_robot(
    portfolio: Portfolio, fund_asset: FundAccountInDB, position_list: List[FundAccountPositionInDB], last_step_solutions: List[SolutionOrderItem]
) -> Robot:
    """构建stralib robot"""
    # 盘中时，如果当日买入股票，可用为0。解决方案是不区分可用和总量的，如果传入的是总量，就会根据总量产生卖出信号，但是实际上是不允许卖出的。为了解决这个问题，我们把总量改成可用
    fund_asset = deepcopy(fund_asset)
    position_list = deepcopy(position_list)  # 构建机器人使用临时的账户数据，防止原始数据被破坏
    for position in position_list:
        position.volume = position.available_volume
    fund_bal, market_value = await update_account_info(last_step_solutions, fund_asset, position_list)
    asset = dict(fundbal=float(fund_bal.to_decimal()), mktval=float(market_value.to_decimal()))
    stocks = await database_stock_list_to_robot(position_list)
    robot_partial = await account_robot_factory(portfolio)
    robot = robot_partial(asset, stocks)
    return robot
