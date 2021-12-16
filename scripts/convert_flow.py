import asyncio
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne

from app import settings
from app.enums.fund_account import CurrencyType, FlowTType
from app.models.fund_account import FundAccountFlowInDB
from app.utils.datetime import date2datetime
from scripts.logging_helper import logger

EXCHANGE_MAPPING = {"0": "CNSESZ", "1": "CNSESH"}

TTYPE_MAPPING = {"buy": FlowTType.BUY, "sell": FlowTType.SELL}


def datetime_str2timestamp(s: str) -> float:
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").timestamp()


async def main(client: AsyncIOMotorClient) -> None:
    """转换资金账户流水格式."""
    old_flow_conn = client[settings.db.DB_NAME][settings.collections.STOCK_LOG]
    new_flow_conn = client[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT_FLOW]
    portfolio_conn = client[settings.db.DB_NAME][settings.collections.PORTFOLIO]

    flow_operations = []

    failed_list = []
    old_flow_rows = old_flow_conn.find()
    old_flow_list = [row async for row in old_flow_rows]
    logging.info(f"共找到{len(old_flow_list)}条流水数据.")
    for row in old_flow_list:
        portfolio = await portfolio_conn.find_one({"_id": row["portfolio"]})
        if not portfolio:
            logging.info(f"未找到组合`{row['portfolio']}`, 已跳过.")
            failed_list.append(str(row["_id"]))
            continue
        if not portfolio["fund_account"][0] or not portfolio["fund_account"][0].get(
            "fundid"
        ):
            logging.info(f"未找到组合`{row['portfolio']}的资金账户`, 已跳过.")
            failed_list.append(str(row["_id"]))
            continue
        logging.info(f"正在处理流水`{row['_id']}`.")
        try:
            quantity = abs(int(float(row["order_quantity"])))
        except Exception:
            continue
        try:
            cost = abs(Decimal(row["filled_amt"])) / quantity
        except InvalidOperation:
            logger.info(f"流水`{row['_id']}`处理错误, 已跳过.")
            failed_list.append(str(row["_id"]))
            continue
        tdate = date2datetime(datetime.strptime(row["trade_date"], "%Y%m%d").date())
        ttype = TTYPE_MAPPING[row["order_direction"]]
        direction = 1 if ttype == FlowTType.BUY else -1
        fund_account_flow_in_db = FundAccountFlowInDB(
            fund_id=portfolio["fund_account"][0]["fundid"],
            symbol=row["symbol"],
            exchange=EXCHANGE_MAPPING[row["exchange"]],
            ttype=ttype,
            stkeffect=direction * quantity,
            cost=str(round(cost, 4)),
            tdate=tdate,
            currency=CurrencyType.CNY,
            ts=datetime_str2timestamp(row["deal_time"])
            if row.get("deal_time")
            else tdate.timestamp(),
            fundeffect=str(-direction * abs(row["fundeffect"])),
            tprice=str(row["trade_price"]),
            total_fee=str(row["total_fee"]),
            commission=str(row["commission"]),
            tax=str(row["stamping"]),
        )
        flow_operations.append(InsertOne(fund_account_flow_in_db.dict(exclude={"id"})))
    if flow_operations:
        await new_flow_conn.bulk_write(flow_operations)
    logger.info(
        f"共处理{len(old_flow_list)}条数据, 成功{len(flow_operations)}条, 失败{len(failed_list)}条."
    )
    logger.info("失败ID列表:\n" + "\n".join(failed_list))


if __name__ == "__main__":
    db_client = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MAX_CONNECTIONS,
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(db_client))
