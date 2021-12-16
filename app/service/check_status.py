from motor.motor_asyncio import AsyncIOMotorClient

from app.crud.base import get_equipment_collection
from app.extentions import logger
from app.global_var import G
from app.service.datetime import get_early_morning, str_of_today


class CheckStatus:
    """检查状态"""

    @classmethod
    async def check_risk_detection_status(
        cls, conn: AsyncIOMotorClient, robot_sid: str
    ):
        """检查是否符合进行风险检测的条件"""
        if await cls.check_time_series_status() and await cls.check_robot_status_by_id(
            conn, robot_sid
        ):
            return True
        return False

    @classmethod
    async def check_robot_status_by_id(cls, conn: AsyncIOMotorClient, sid: str):
        """检查机器人状态"""
        robot = await get_equipment_collection(conn).find_one({"标识符": sid})
        if not robot or robot.get("计算时间") != get_early_morning():
            return False
        return True

    @classmethod
    async def check_equip_status(cls, conn: AsyncIOMotorClient):
        """检查装备状态"""
        equip_list = get_equipment_collection(conn).find({"状态": "已上线"})
        today = get_early_morning()
        try:
            data_list = [x async for x in equip_list if x.get("计算时间") != today]
        except Exception as e:
            logger.error(f"【获取计算时间失败】 {e}")
            return False
        if data_list:
            return False
        return True

    @classmethod
    async def check_equip_status_by_sid(cls, conn: AsyncIOMotorClient, sid_list: list):
        """检查装备状态"""
        equip_list = get_equipment_collection(conn).find({"状态": "已上线"})
        today = get_early_morning()
        data_list = [
            x
            async for x in equip_list
            if x["标识符"] in sid_list and x.get("计算时间") != today
        ]
        if data_list:
            return False
        return True

    @classmethod
    async def check_time_series_status(cls):
        """检查同步时点数据状态"""
        key = f"{str_of_today()}_time_series_data"
        item = await G.scheduler_redis.get(key)
        if not item:
            return False
        return True

    @classmethod
    async def check_ability_status(cls):
        """检查战斗力计算是否完成"""
        key = f"{str_of_today()}_ability"
        item = await G.scheduler_redis.get(key)
        if not item:
            return False
        return True

    @classmethod
    async def check_liquidate_dividend_status(cls):
        """检查清算分红任务是否完成"""
        key = f"{str_of_today()}_liquidate_dividend"
        item = await G.scheduler_redis.get(key)
        if not item:
            return False
        return True

    @classmethod
    async def check_liquidate_dividend_flow_status(cls):
        """检查清算分红流水任务是否完成"""
        key = f"{str_of_today()}_liquidate_dividend_flow"
        item = await G.scheduler_redis.get(key)
        if not item:
            return False
        return True

    @classmethod
    async def check_liquidate_dividend_tax_status(cls):
        """检查清算分红扣税任务是否完成"""
        key = f"{str_of_today()}_liquidate_dividend_tax"
        item = await G.scheduler_redis.get(key)
        if not item:
            return False
        return True
