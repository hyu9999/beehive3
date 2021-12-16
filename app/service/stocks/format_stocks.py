from app import settings
from app.enums.log import 买卖方向
from app.enums.order import EntrustOrderStatus
from app.models.log import StockLog
from app.models.rwmodel import PyObjectId
from app.outer_sys.hq import get_security_info
from app.schema.log import ManualStockInCreate


async def manual_stock_format(order: ManualStockInCreate, assets: dict) -> StockLog:
    """手工录入订单格式化"""
    security = await get_security_info(order.symbol, order.exchange)
    order.symbol_name = order.symbol_name or security.symbol_name
    order.trade_time = order.trade_time or "000000"

    trade_amount = order.trade_volume * order.trade_price
    commission = settings.commission * trade_amount
    if order.order_direction == 买卖方向.buy:
        stkeffect = order.trade_volume
        stamping = 0
        ttype = "3"
    else:
        stamping = settings.tax * trade_amount
        stkeffect = -order.trade_volume
        ttype = "4"
    total_fee = commission + stamping
    filled_amt = trade_amount + total_fee
    fundeffect = filled_amt if order.order_direction == 买卖方向.buy else -1 * filled_amt
    extra_params = {
        "portfolio": order.portfolio,
        "order_date": order.trade_date,
        "trade_time": order.trade_time,
        "order_time": order.trade_time,
        "order_price": order.trade_price,
        "order_status": EntrustOrderStatus.DEAL.value,
        "order_quantity": order.trade_volume,
        "order_volume": order.trade_volume,
        "order_id": str(PyObjectId()),
        "stkeffect": stkeffect,
        "filled_amt": filled_amt,
        "fundeffect": fundeffect,
        "transfer_fee": 0,
        "settlement_fee": 0,
        "commission": commission,  # 佣金
        "stamping": stamping,  # 印花税
        "total_fee": total_fee,  # 总费用
        "ttype": ttype,
        "stock_quantity": order.trade_volume,
        "position_change": order.trade_price * order.trade_volume / (assets["total_capital"] + order.trade_price * order.trade_volume),
    }
    extra_params.update(order.dict())
    return StockLog(**extra_params)
