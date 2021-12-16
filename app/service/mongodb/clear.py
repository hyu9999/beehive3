from typing import List

import typer

from app.crud.base import (
    get_collection_by_config,
    get_portfolio_collection,
    get_user_message_collection,
    get_equipment_collection,
    get_robots_collection,
    get_portfolio_analysis_collection,
    get_position_time_series_data_collection,
    get_fund_time_series_data_collection,
    get_portfolio_assessment_time_series_data_collection,
    get_fund_account_collection,
    get_fund_account_flow_collection,
    get_fund_account_position_collection,
    get_favorite_stock_collection,
)
from app.db.mongodb import db
from app.schedulers import logger

COL_LIST = ["portfolio", "equipment", "robot"]


async def clear_mongodb(col_list: List[str] = None):
    col_list = col_list or COL_LIST
    clear_col = ClearCollection()
    for func in col_list:
        logger.info(f"clear {func}")
        await getattr(clear_col, f"clear_{func}")()


class ClearCollection:
    def __init__(self):
        self.client = db.client

    async def clear_portfolio(self, filters: dict = None):
        filters = filters or {"status": "closed"}
        async for p in get_portfolio_collection(self.client).find(filters):
            pid = p["_id"]
            typer.echo(f"组合--{pid}")
            fund_id = p["fund_account"][0]["fundid"]
            typer.echo("clear 组合及扩展信息")
            await get_portfolio_collection(self.client).delete_one({"_id": pid})
            await get_portfolio_analysis_collection(self.client).delete_many({"portfolio": pid})
            typer.echo("clear 时点数据表")
            await get_position_time_series_data_collection(self.client).delete_many({"fund_id": fund_id})
            await get_fund_time_series_data_collection(self.client).delete_many({"fund_id": fund_id})
            await get_portfolio_assessment_time_series_data_collection(self.client).delete_many({"portfolio": pid})
            typer.echo("clear 清理交易相关数据")
            await get_fund_account_collection(self.client).delete_many({"_id": fund_id})
            await get_fund_account_flow_collection(self.client).delete_many({"fund_id": fund_id})
            await get_fund_account_position_collection(self.client).delete_many({"fund_id": fund_id})
            typer.echo("clear 清理日志")
            await get_user_message_collection(self.client).delete_many({"category": "portfolio", "data_info": str(pid)})

    async def clear_equipment(self, filters: dict = None):
        filters = filters or {"状态": "已删除"}
        async for p in get_equipment_collection(self.client).find(filters):
            sid = p["标识符"]
            typer.echo(f"装备--{sid}")
            await get_equipment_collection(self.client).delete_one({"标识符": sid})
            typer.echo("clear 装备日志")
            await get_user_message_collection(self.client).delete_many({"category": "equipment", "data_info": sid})
            typer.echo("clear 自选股")
            await get_favorite_stock_collection(self.client).delete_many({"category": "equipment", "sid": sid})
            typer.echo("clear 装备策略数据")
            if p["分类"] in ["选股", "择时", "大类资产配置", "基金定投"]:
                await get_collection_by_config(self.client, f"{p['分类']}回测信号collection名").delete_many({"标识符": sid})
                await get_collection_by_config(self.client, f"{p['分类']}回测指标collection名").delete_many({"标识符": sid})
                await get_collection_by_config(self.client, f"{p['分类']}回测评级collection名").delete_many({"标识符": sid})
                await get_collection_by_config(self.client, f"{p['分类']}实盘信号collection名").delete_many({"标识符": sid})
                await get_collection_by_config(self.client, f"{p['分类']}实盘指标collection名").delete_many({"标识符": sid})

    async def clear_robot(self, filters: dict = None):
        filters = filters or {"状态": "已删除"}
        async for p in get_robots_collection(self.client).find(filters):
            sid = p["标识符"]
            typer.echo(f"机器人--{sid}")
            await get_robots_collection(self.client).delete_one({"标识符": sid})
            typer.echo("clear 自选股")
            await get_favorite_stock_collection(self.client).delete_many({"category": "robot", "sid": sid})
            typer.echo("clear 机器人日志")
            await get_user_message_collection(self.client).delete_many({"category": "robot", "data_info": sid})
            typer.echo("clear 机器人策略数据")
            await get_collection_by_config(self.client, "机器人回测信号collection名").delete_many({"标识符": sid})
            await get_collection_by_config(self.client, "机器人回测指标collection名").delete_many({"标识符": sid})
            await get_collection_by_config(self.client, "机器人回测评级collection名").delete_many({"标识符": sid})
            await get_collection_by_config(self.client, "机器人实盘信号collection名").delete_many({"标识符": sid})
            await get_collection_by_config(self.client, "机器人实盘指标collection名").delete_many({"标识符": sid})
