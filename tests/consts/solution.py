import datetime

from bson import Decimal128, ObjectId

from app.enums.fund_account import CurrencyType, Exchange
from app.enums.log import 买卖方向
from app.enums.order import 订单状态
from app.enums.stock import 股票市场Enum
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.schema.order import SolutionOrderItem

solution_order_list = [
    SolutionOrderItem(
        symbol="600100",
        exchange=股票市场Enum.上海,
        symbol_name="测试股票",
        order_id="string",
        fund_id="string",
        status=订单状态.waiting,
        finished_quantity=0,
        average_price=11,
        quantity=100,
        operator=买卖方向.sell,
        price=10,
        reason="string",
        date="string",
        opinion="string",
    ),
    SolutionOrderItem(
        symbol="600100",
        exchange=股票市场Enum.上海,
        symbol_name="测试股票",
        order_id="string",
        fund_id="string",
        status=订单状态.waiting,
        finished_quantity=0,
        average_price=11,
        quantity=100,
        operator=买卖方向.sell,
        price=-1,
        reason="string",
        date="string",
        opinion="string",
    ),
    SolutionOrderItem(
        symbol="600100",
        exchange=股票市场Enum.上海,
        symbol_name="测试股票",
        order_id="string",
        fund_id="string",
        status=订单状态.waiting,
        finished_quantity=0,
        average_price=0.0,
        quantity=100,
        operator=买卖方向.buy,
        price=10,
        reason="string",
        date="string",
        opinion="string",
    ),
    SolutionOrderItem(
        symbol="600100",
        exchange=股票市场Enum.上海,
        symbol_name="测试股票",
        order_id="string",
        fund_id="string",
        status=订单状态.waiting,
        finished_quantity=0,
        average_price=0.0,
        quantity=0,
        operator=买卖方向.buy,
        price=-1,
        reason="string",
        date="string",
        opinion="string",
    ),
]
position_list = [
    FundAccountPositionInDB(
        fund_id=str(ObjectId()),
        symbol="601816",
        exchange=Exchange.CNSESH,
        volume=30,
        available_volume=30,
        cost=Decimal128("5.92"),
        first_buy_date=datetime.datetime(
            2020, 12, 4, 10, 22, 51, 571000, tzinfo=datetime.timezone.utc
        ),
        count=0,
        current_price=0,
        created_at=datetime.datetime(2021, 4, 25, 6, 7, 45, 612856),
        updated_at=datetime.datetime(2021, 4, 25, 6, 7, 45, 612859),
        id=ObjectId("6085073178a06c96575604b5"),
    )
]
fund_asset = FundAccountInDB(
    capital=Decimal128("1000000.0"),
    assets=Decimal128("1000000"),
    cash=Decimal128("1000000"),
    securities=Decimal128("0.00"),
    commission=Decimal128("0.0003"),
    tax_rate=Decimal128("0.001"),
    slippage=Decimal128("0.01"),
    ts_data_sync_date=datetime.datetime(2021, 4, 23, 0, 0),
    currency=CurrencyType.CNY,
    created_at=datetime.datetime(2021, 4, 25, 6, 7, 34, 591115),
    updated_at=datetime.datetime(2021, 4, 25, 6, 7, 34, 591120),
    id=ObjectId("5f8163f4ef78c0513b8724d1"),
)
