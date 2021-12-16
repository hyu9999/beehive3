from typing import Dict, Any

from stralib.fb.robot_conf import get_robot_details

from app.db.mongodb import db

from app.crud.robot import 查询某机器人信息
from app.enums.robot import 卖出筛选器, 买入筛选器, 保证持仓数量筛选器, 减仓模式
from app.schema.robot import 机器人inResponse


class RobotTools:
    @classmethod
    async def get_portfolio_robot(cls, sid: str) -> Dict[str, Any]:
        """获取组合的robot"""
        robot = await 查询某机器人信息(db.client, sid, show_detail=False)
        return await cls.format_robot(robot)

    @staticmethod
    async def format_robot(robot: 机器人inResponse) -> Dict[str, Any]:
        """机器人字段中文变英文"""
        formatted_robot = robot.dict()
        formatted_robot["id"] = robot.标识符
        formatted_robot["name"] = robot.名称
        principle_config = {i.唯一名称: i.配置值 for i in robot.原则配置}
        formatted_robot["stopup"] = float(principle_config.get("stopup", 0.15))
        formatted_robot["stopdown"] = float(principle_config.get("stopdown", 0.08))
        formatted_robot["reduce"] = robot.减仓模式[0].value
        formatted_robot["risk_sid_list"] = robot.风控装备列表
        formatted_robot["timing_sid_list"] = robot.择时装备列表
        formatted_robot["stock_sid_list"] = robot.选股装备列表
        formatted_robot["tstock_tsid_list"] = robot.交易装备列表
        formatted_robot["sold_filter_strategy_list"] = [卖出筛选器.__dict__[i] for i in robot.卖出筛选器]
        formatted_robot["buy_filter_strategy_list"] = [买入筛选器.__dict__[i] for i in robot.买入筛选器]
        formatted_robot["filter_buy_stock_symbol"] = [保证持仓数量筛选器.__dict__[i] for i in robot.保证持仓数量筛选器]
        formatted_robot["reduce"] = [减仓模式[i].value for i in robot.减仓模式][0]  # 目前减仓模式在数据库中仅存储一条数据，且stralib中reduce为str
        try:
            formatted_robot["detail"] = get_robot_details(robot.标识符)
        except StopIteration:
            formatted_robot["detail"] = ""
        return formatted_robot
