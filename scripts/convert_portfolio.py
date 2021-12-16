import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

from app import settings
from app.enums.portfolio import PortfolioCategory
from scripts.logging_helper import logger


async def main(client: AsyncIOMotorClient) -> None:
    """转换组合模型."""
    portfolio_conn = client[settings.db.DB_NAME][settings.collections.PORTFOLIO]

    portfolio_rows = portfolio_conn.find()
    portfolio_list = [row async for row in portfolio_rows]
    logging.info(f"共找到{len(portfolio_list)}个组合.")
    operations = []
    for portfolio in portfolio_list:
        logging.info(f"正在处理组合`{portfolio['_id']}`.")
        # 去除字段
        unset = {"stats_data": "", "broker": "", "import_date": "", "sync_type": ""}
        # 修改值
        set_ = {
            "fund_account": [{**portfolio["fund_account"], "currency": "CNY"}],
            "category": PortfolioCategory.SimulatedTrading.value
            if portfolio.get("sync_type") == "auto"
            else PortfolioCategory.ManualImport.value,
        }
        operations.append(
            UpdateOne({"_id": portfolio["_id"]}, {"$set": set_, "$unset": unset})
        )
    if operations:
        await portfolio_conn.bulk_write(operations)
    logger.info(f"共处理{len(portfolio_list)}条数据, 成功{len(operations)}条.")


if __name__ == "__main__":
    db_client = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MAX_CONNECTIONS,
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(db_client))
