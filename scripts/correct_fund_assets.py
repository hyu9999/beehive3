import asyncio
from datetime import timedelta

from bson import ObjectId, Decimal128
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import FastTdate

from app import settings
from app.enums.fund_account import FlowTType
from app.models.fund_account import FundAccountFlowInDB, FundAccountInDB
from app.outer_sys.hq.events import set_hq_source, connect_hq2reids, close_hq2redis_conn
from app.service.fund_account.fund_account import update_position_by_flow, update_fund_account_by_flow


async def main(client: AsyncIOMotorClient) -> None:
    await set_hq_source()
    await connect_hq2reids()

    portfolio_conn = client[settings.db.DB_NAME][settings.collections.PORTFOLIO]
    flow_conn = client[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT_FLOW]
    fund_account_conn = client[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT]
    position_conn = client[settings.db.DB_NAME][settings.collections.FUND_ACCOUNT_POSITION]

    portfolio_rows = portfolio_conn.find({"status": "running", "category": "ManualImport"})
    portfolio_list = [row async for row in portfolio_rows]
    print(f"共找到{len(portfolio_list)}个组合.")

    for portfolio in portfolio_list:
        print(f"正在处理组合`{portfolio['_id']}`的数据.")
        fund_id = portfolio["fund_account"][0]["fundid"]
        # 删除分红扣税流水
        await flow_conn.delete_many({"fund_id": fund_id, "ttype": {"$in": ["5", "6"]}})

        # 删除用户持仓
        await position_conn.delete_many({"fund_id": fund_id})

        capital = str(portfolio["initial_funding"])
        import_date_raw = portfolio["import_date"] + timedelta(days=1)
        import_date = FastTdate.last_tdate(import_date_raw)

        # 重置用户资产
        await fund_account_conn.update_one(
            {"_id": ObjectId(fund_id)},
            {
                "$set": {
                    "assets": capital,
                    "cash": capital,
                    "securities": Decimal128("0"),
                    "ts_data_sync_date": import_date
                }
            }
        )

        flow_rows = flow_conn.find({"fund_id": fund_id})
        async for flow in flow_rows.sort("tdate"):
            fund_account_row = await fund_account_conn.find_one({"_id": ObjectId(fund_id)})
            fund_account = FundAccountInDB(**fund_account_row)
            flow_in_db = FundAccountFlowInDB(**flow)

            if flow_in_db.ttype not in [FlowTType.DEPOSIT, FlowTType.WITHDRAW]:
                await update_position_by_flow(client, flow_in_db)
            await update_fund_account_by_flow(client, fund_account, flow_in_db)

    await close_hq2redis_conn()


if __name__ == "__main__":
    db_client = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MAX_CONNECTIONS,
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(db_client))
