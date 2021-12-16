import asyncio
import logging
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

from app import settings
from app.enums.portfolio import PortfolioCategory
from app.utils.datetime import date2datetime
from scripts.logging_helper import logger


async def main(client: AsyncIOMotorClient) -> None:
    """添加组合的持仓导入时间."""
    portfolio_conn = client[settings.db.DB_NAME][settings.collections.PORTFOLIO]
    flow_conn = client[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT_FLOW]

    portfolio_rows = portfolio_conn.find()
    portfolio_list = [row async for row in portfolio_rows]
    logging.info(f"共找到{len(portfolio_list)}个组合.")
    operations = []
    for portfolio in portfolio_list:
        logging.info(f"正在处理组合`{portfolio['_id']}`.")
        try:
            fund_account = portfolio["fund_account"][0]
            if portfolio["category"] == PortfolioCategory.SimulatedTrading:
                import_date = date2datetime(portfolio["create_date"].date())
            else:
                flow_list = flow_conn.find({"fund_id": fund_account["fundid"]})
                import_date = min(
                    [flow["tdate"] async for flow in flow_list]
                    + [portfolio["create_date"]]
                )
        except KeyError as e:
            logging.info(f"处理组合`{portfolio['_id']}`持仓导入时间失败, 已跳过({e}).")
            continue
        else:
            if import_date < datetime.fromisoformat("2021-01-01"):
                set_ = {
                    "import_date": date2datetime(
                        import_date.date() - timedelta(days=1)
                    ),
                    "status": "closed",
                }
                operations.append(UpdateOne({"_id": portfolio["_id"]}, {"$set": set_}))
            else:
                set_ = {
                    "import_date": date2datetime(import_date.date() - timedelta(days=1))
                }
                operations.append(UpdateOne({"_id": portfolio["_id"]}, {"$set": set_}))
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
