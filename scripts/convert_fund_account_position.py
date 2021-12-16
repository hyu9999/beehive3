import asyncio
import logging

from pymongo import InsertOne
from motor.motor_asyncio import AsyncIOMotorClient

from scripts.logging_helper import logger
from app import settings
from app.models.fund_account import FundAccountPositionInDB
from app.service.datetime import get_early_morning

EXCHANGE_MAPPING = {
    "0": "CNSESZ",
    "1": "CNSESH"
}


async def main(client: AsyncIOMotorClient) -> None:
    """转换手动导入资金账户持仓格式."""
    old_fund_account_position_conn = client[settings.db.DB_NAME][settings.collections.TS_POSITION]
    new_fund_account_position_conn = client[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT_POSITION]
    portfolio_conn = client[settings.db.DB_NAME][settings.collections.PORTFOLIO]

    fund_account_position_rows = old_fund_account_position_conn.find()
    fund_account_position_list = [fund_account async for fund_account in fund_account_position_rows]
    logging.info(f"共找到{len(fund_account_position_list)}条持仓数据.")
    operations = []
    failed_list = []
    for position in fund_account_position_list:
        logging.info(f"正在处理持仓`{position['_id']}`.")
        portfolio = await portfolio_conn.find_one({"_id": position["portfolio"]})
        if not portfolio:
            logger.info(f"未找到持仓`{position['_id']}`所属组合`{position['portfolio']}`, 已跳过处理该持仓.")
            failed_list.append(str(position["_id"]))
            continue
        if not portfolio['fund_account'][0] or not portfolio['fund_account'][0].get("fundid"):
            logging.info(f"未找到持仓`{position['_id']}`所属组合`{position['portfolio']}的资金账户`, 已跳过.")
            failed_list.append(str(position["_id"]))
            continue
        new_position = FundAccountPositionInDB(
            fund_id=portfolio["fund_account"][0]["fundid"],
            symbol=position["symbol"],
            exchange=EXCHANGE_MAPPING[position["exchange"]],
            volume=position["stock_quantity"],
            cost=position["share_cost_price"],
            first_buy_date=get_early_morning(position["buy_date"])
        )
        operations.append(InsertOne(new_position.dict(exclude={"id"})))
    if operations:
        await new_fund_account_position_conn.bulk_write(operations)
    logger.info(f"共处理{len(fund_account_position_list)}条数据, 成功{len(operations)}条, 失败{len(failed_list)}条.")
    logger.info("失败ID列表:\n" + "\n".join(failed_list))


if __name__ == "__main__":
    db_client = AsyncIOMotorClient(
        settings.db.MONGODB_URL, maxPoolSize=settings.db.MAX_CONNECTIONS, minPoolSize=settings.db.MAX_CONNECTIONS
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(db_client))
