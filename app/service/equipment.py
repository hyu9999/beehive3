import time
from datetime import datetime
from typing import List, Dict, Optional

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from stralib import get_strategy_signal, FastTdate

from app import settings
from app.core.errors import ParamsError, EquipTooMany
from app.crud.base import get_equipment_collection, get_robots_collection, get_portfolio_collection
from app.enums.equipment import 装备分类_3, 装备分类转换
from app.models.base.equipment import 装备运行数据
from app.schema.equipment import 装备InCreate, SymbolGradeStrategyWordsInresponse
from app.schema.user import User
from app.service.datetime import str_of_today, get_early_morning


async def 生成装备标识符(分类: 装备分类_3, db: AsyncIOMotorClient):
    prefix = f"{装备分类转换[分类]}{int(time.mktime(datetime.utcnow().timetuple()))}"
    suffix = "1"
    filters = {"标识符": {"$regex": f"^{prefix}.*"}}
    cnt = await get_equipment_collection(db).count_documents(filters)
    if cnt:
        queryset = get_equipment_collection(db).find(filters).sort("标识符", pymongo.DESCENDING)
        async for x in queryset:
            suffix = int(x["标识符"][-2:]) + 1
            break
    标识符 = f"{prefix}{str(suffix).zfill(2)}"
    return 标识符


async def 装备数量限制(装备分类: 装备分类_3, user: User, db: AsyncIOMotorClient):
    """检查用户装备数量是否超出限制"""
    if not user.roles[0] == "超级用户":
        prefix = f"{装备分类转换[装备分类]}"
        filters = {"作者": user.username, "标识符": {"$regex": f"^{prefix}.*"}, "状态": {"$nin": ["已删除"]}}
        cnt = await get_equipment_collection(db).count_documents(filters)
        if cnt >= settings.num_limit[user.roles[0]]["equipment"]:
            raise EquipTooMany(message=f"创建装备数达到上限，最多只能创建{settings.num_limit[user.roles[0]]['equipment']}个")


async def 是否被机器人使用(sid: str, db):
    flag = False
    robots = get_robots_collection(db).find({"状态": {"$nin": ["已删除", "已下线"]}})
    if sid.startswith("11"):
        async for robot in robots:
            if sid in robot["风控包列表"]:
                flag = True
                break
    else:
        if sid.startswith("01"):
            equipment_type = "交易"
        elif sid.startswith("02"):
            equipment_type = "选股"
        elif sid.startswith("03"):
            equipment_type = "择时"
        elif sid.startswith("04"):
            equipment_type = "风控"
        else:
            raise RuntimeError("错误的标识符")
        async for robot in robots:
            if sid in robot[f"{equipment_type}装备列表"]:
                flag = True
                break
    return flag


async def 是否被机器人订阅(sid: str, db: AsyncIOMotorClient):
    equipment = await get_equipment_collection(db).find_one({"标识符": sid})
    if equipment.get("订阅人数", 0) > 0:
        return True
    return False


async def get_grade_strategy_words_by_time(
    conn: AsyncIOMotorClient, risk_sid_list: List[str], symbol_list: List[str], start: str = None, end: str = None
) -> List[SymbolGradeStrategyWordsInresponse]:
    """
    查询某段时间内用户的股票池中有风险的股票及对应风控策略话术
    Parameters
    ----------
    conn    数据库client
    risk_sid_list  风控装备标识符列表
    symbol_list  用户股票池
    start   开始日期
    end     结束日期

    Returns
    -------
    List[SymbolGradeStrategyWordsInresponse]
    """
    end = end or str_of_today()
    start = start or str_of_today()
    end = end if FastTdate.is_tdate(end) else FastTdate.last_tdate(end)
    start = start if FastTdate.is_tdate(start) else FastTdate.last_tdate(start)
    if end == start == str_of_today() and datetime.now().hour < 19:
        end = start = FastTdate.last_tdate(end)
    result = []
    for symbol in symbol_list:
        grade_list = []
        for sid in risk_sid_list:
            try:
                df = get_strategy_signal(sid, start, end)
                grade = df[df["symbol"].isin([symbol])].iloc[-1]["grade"]
            except (IndexError, KeyError):
                continue
            if grade:
                equipment = await get_equipment_collection(conn).find_one({"标识符": sid})
                strategy_words = equipment.get("策略话术")
            else:
                strategy_words = None
            grade_list.append({"grade": grade, "strategy_words": strategy_words})
        result.append(SymbolGradeStrategyWordsInresponse(**{"symbol": symbol, "grade_strategy_word": grade_list}))
    return result


def format_trade_equipment_strategy_word(reason: str, strategy_word: Optional[Dict[str, str]]) -> Optional[str]:
    """
    拼装交易装备的策略话术
    Parameters
    ----------
    reason "('买1',)","('卖1',)","('0',)"
    strategy_word 策略话术

    Returns
    -------

    """
    if not strategy_word:
        return strategy_word
    tuple_reason = eval(reason)
    if len(tuple_reason) == 1:
        reason_str = reason
    elif len(tuple_reason) == 2:
        # 扩展代码，目前业务暂未支持，tuple_reason中第二个元素可用于扩展话术value值，eg:{"('卖1',)": "辅助线下穿济安线，形成死叉，看空{value1}"}
        reason_str = f"('{tuple_reason[0]}',)"
    else:
        raise ParamsError(message="参数错误：交易装备拼装策略话术，传入reason不符合要求！")
    ret_data = [v for k, v in strategy_word.items() if k == reason_str][0]
    return ret_data


async def 计算装备运行数据(db: AsyncIOMotorClient, 标识符: str) -> Dict:
    """

    Parameters
    ----------
    db
    标识符

    Returns
    -------
    装备运行数据
    """
    data = 装备运行数据()
    equipment = await get_equipment_collection(db).find_one({"标识符": 标识符})
    data.运行天数 = (get_early_morning() - equipment["上线时间"]).days
    if 标识符.startswith("11"):
        data.累计产生信号数 = sum([get_strategy_signal(x, equipment["上线时间"], get_early_morning()).shape[0] for x in equipment["装备列表"]])
        robot_sid_list = await get_robots_collection(db).distinct("标识符", {"风控装备列表": {"$all": equipment["装备列表"]}})
    else:
        data.累计产生信号数 = get_strategy_signal(标识符, equipment["上线时间"], get_early_morning()).shape[0]
        robot_sid_list = await get_robots_collection(db).distinct("标识符", {f"{equipment['分类']}装备列表": 标识符})
    data.累计服务人数 = await get_portfolio_collection(db).count_documents({"robot": {"$in": robot_sid_list}})
    return data.dict()
