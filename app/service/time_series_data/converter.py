from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from bson import Decimal128, ObjectId
from pydantic import ValidationError

from app.enums.fund_account import CurrencyType, Exchange, FlowTType
from app.extentions import logger
from app.models.base.time_series_data import Position
from app.models.fund_account import (
    FundAccountFlowInDB,
    FundAccountInDB,
    FundAccountPositionInDB,
)
from app.models.time_series_data import (
    FundTimeSeriesDataInDB,
    PositionTimeSeriesDataInDB,
)
from app.outer_sys.hq import get_security_price
from app.service.datetime import get_early_morning
from app.utils.exchange import convert_exchange


def field_converter(d: dict) -> dict:
    """转换字段类型.

    Decimal128 => float
    Exchange => str
    FlowTType => str
    CurrencyType => str
    ObjectId => str
    """
    for key, v in d.items():
        if isinstance(v, Decimal128):
            d[key] = float(v.to_decimal())
        if isinstance(v, Exchange):
            d[key] = v.value
        if isinstance(v, FlowTType):
            d[key] = v.value
        if isinstance(v, CurrencyType):
            d[key] = v.value
        if isinstance(v, ObjectId):
            d[key] = str(v)
    return d


async def position2time_series(
    position_list: List[FundAccountPositionInDB], fund_id: str, tdate: datetime
) -> PositionTimeSeriesDataInDB:
    """资金账户持仓转为持仓时点数据格式."""
    position_time_series_data = PositionTimeSeriesDataInDB(
        fund_id=fund_id, tdate=tdate, position_list=[]
    )
    if position_list:
        for position in position_list:
            try:
                security = await get_security_price(
                    symbol=position.symbol,
                    exchange=convert_exchange(position.exchange, to="beehive"),
                )
            # 触发该异常可能由于股票已退市, 所以按0处理
            except ValidationError as e:
                logger.warning(f"查询股票`{position.symbol}`价格失败, 价格已按0处理({e}).")
                market_value = Decimal(0)
            else:
                market_value = security.current * position.volume
            position_time_series_data.position_list.append(
                Position(
                    symbol=position.symbol,
                    market=position.exchange,
                    stkbal=position.volume,
                    mktval=market_value,
                    buy_date=position.first_buy_date,
                )
            )
    return position_time_series_data


def fund2time_series(
    fund_account: FundAccountInDB, tdate: datetime
) -> FundTimeSeriesDataInDB:
    """资金账户资产转为资产时点数据格式."""
    return FundTimeSeriesDataInDB(
        fund_id=str(fund_account.id),
        tdate=tdate,
        fundbal=fund_account.cash,
        mktval=fund_account.securities,
    )


def position_time_series_data2ability(
    position_time_series_data: PositionTimeSeriesDataInDB,
) -> dict:
    """持仓时点数据转换为战斗力所需格式.

    Returns
    -------
    {
        "600519": [{
            "symbol": "600519",
            "exchange": "CNSESH",
            "stock_quantity": "10000",
            "market_value": "100000"
        }]
    }
    """
    field_mapping = {
        "exchange": "market",
        "stock_quantity": "stkbal",
        "market_value": "mktval",
    }
    ability_dict = {}
    if position_time_series_data.position_list:
        for position in position_time_series_data.position_list:
            position = dict(position)
            for k, v in field_mapping.items():
                position[k] = position.pop(v)
                ability_dict[position["symbol"]] = [field_converter(position)]
    return ability_dict


def fund_time_series_data2ability(
    fund_time_series_data: FundTimeSeriesDataInDB,
) -> dict:
    """资产时点数据转换为战斗力所需格式."""
    field_mapping = {"fund_balance": "fundbal", "market_value": "mktval"}
    ability_dict = fund_time_series_data.dict()
    for k, v in field_mapping.items():
        ability_dict[k] = ability_dict.pop(v)
    return field_converter(ability_dict)


def ability2fund_time_series_data(
    ability_dict: Dict[datetime, dict]
) -> List[FundTimeSeriesDataInDB]:
    """战斗力数据转换为资产时点数据."""
    fund_time_series_data_list = []
    for tdate, item in ability_dict.items():
        fund_time_series_data_list.append(
            FundTimeSeriesDataInDB(
                fund_id=item["fund_id"],
                tdate=tdate,
                fundbal=str(item["fund_balance"]),
                mktval=str(item["market_value"]),
            )
        )
    return fund_time_series_data_list


def ability2position_time_series_data(
    fund_id: str, ability_dict: Dict[datetime, dict]
) -> List[PositionTimeSeriesDataInDB]:
    """战斗力数据转换为持仓时点数据."""
    position_time_series_data_list = []
    for tdate, item in ability_dict.items():
        position_time_series_data = PositionTimeSeriesDataInDB(
            fund_id=fund_id, tdate=tdate, position_list=[]
        )
        for symbol, position_dict in item.items():
            position_dict = position_dict[0]
            position_time_series_data.position_list.append(
                Position(
                    symbol=symbol,
                    market=position_dict["exchange"],
                    stkbal=position_dict["stock_quantity"],
                    mktval=position_dict["market_value"],
                    buy_date=position_dict.get("buy_date"),
                )
            )
        position_time_series_data_list.append(position_time_series_data)
    return position_time_series_data_list


def pt_flow2beehive_flow(flow: dict, currency: CurrencyType) -> FundAccountFlowInDB:
    trade_category_mapping = {"buy": "3", "sell": "4", "dividend": "5", "tax": "6"}
    ttype = trade_category_mapping[flow["trade_category"]]
    direction = 1 if flow["trade_category"] == "buy" else -1
    if Decimal(flow["amount"]) == Decimal("0") or flow["volume"] == 0:
        cost = Decimal("0")
    else:
        cost = abs(Decimal(flow["amount"])) / abs(flow["volume"])
    deal_time = flow["deal_time"]
    if isinstance(deal_time, str):
        deal_time = datetime.strptime(deal_time[:19], "%Y-%m-%dT%H:%M:%S")
    return FundAccountFlowInDB(
        fund_id=flow["user"],
        symbol=flow["symbol"],
        exchange=convert_exchange(flow["exchange"], to="stralib"),
        ttype=ttype,
        stkeffect=direction * abs(flow["volume"]),
        cost=cost,
        tdate=get_early_morning(deal_time),
        currency=currency,
        ts=deal_time.timestamp(),
        fundeffect=-direction * abs(Decimal(flow["amount"])),
        tprice=flow["sold_price"],
        total_fee=flow["costs"]["total"],
        commission=flow["costs"]["commission"],
        tax=flow["costs"]["tax"],
    )
