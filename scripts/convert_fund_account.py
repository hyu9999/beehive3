import asyncio
import logging

from pymongo import InsertOne, UpdateOne
from stralib import FastTdate
from motor.motor_asyncio import AsyncIOMotorClient

from scripts.logging_helper import logger
from app import settings
from app.models.fund_account import FundAccountInDB
from app.models.rwmodel import PyObjectId


async def main(client: AsyncIOMotorClient) -> None:
    """转换手动导入资金账户资产格式."""
    old_fund_account_conn = client[settings.db.DB_NAME][settings.collections.TS_ASSETS]
    new_fund_account_conn = client[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT]
    portfolio_conn = client[settings.db.DB_NAME][settings.collections.PORTFOLIO]

    fund_account_rows = old_fund_account_conn.find()
    fund_account_list = [fund_account async for fund_account in fund_account_rows]
    logging.info(f"共找到{len(fund_account_list)}个手动导入资金账户.")
    operations = []
    portfolio_operations = []
    failed_list = []
    for fund_account in fund_account_list:
        logging.info(f"正在处理资金账户`{fund_account['_id']}`.")
        portfolio = await portfolio_conn.find_one({"_id": PyObjectId(fund_account["portfolio"])})
        if not portfolio:
            logger.info(f"未找到资金账户`{fund_account['_id']}所属组合`, 已跳过.")
            failed_list.append(str(fund_account["_id"]))
            continue
        new_fund_account = FundAccountInDB(
            capital=str(fund_account["capital"]),
            assets=str(fund_account["total_capital"]),
            cash=str(fund_account["fund_available"]),
            securities=str(fund_account["market_value"]),
            ts_data_sync_date=FastTdate.last_tdate(fund_account["created_at"])
        )
        row = await new_fund_account_conn.insert_one(new_fund_account.dict(exclude={"id"}))
        portfolio_operations.append(
            UpdateOne({"_id": portfolio["_id"]}, {"$set": {"fund_account.0.fundid": str(row.inserted_id)}})
        )
        operations.append(InsertOne(new_fund_account.dict()))
    if portfolio_operations:
        await portfolio_conn.bulk_write(portfolio_operations)
    logger.info(f"共处理{len(fund_account_list)}条数据, 成功{len(operations)}条.")


if __name__ == "__main__":
    db_client = AsyncIOMotorClient(
        settings.db.MONGODB_URL, maxPoolSize=settings.db.MAX_CONNECTIONS, minPoolSize=settings.db.MAX_CONNECTIONS
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(db_client))
