from collections import defaultdict, namedtuple
from datetime import datetime
from smtplib import SMTPResponseException
from typing import Union

import pandas as pd
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne
from stralib import FastTdate

from app import settings
from app.core.errors import NoUserError
from app.crud.base import get_strategy_publish_log_collection, get_collection_by_config, get_robots_collection, get_equipment_collection
from app.crud.equipment import 查询装备列表
from app.crud.robot import 查询机器人列表
from app.crud.user import get_manufacturer_user
from app.db.mongodb import db
from app.enums.common import 回测评级数据集
from app.enums.equipment import 装备分类转换, 装备分类_3
from app.enums.publish import 错误信息错误类型enum
from app.extentions import logger
from app.models.base.publish import StrategyPublishLog
from app.outer_sys.message.adaptor.mail import SendEmail
from app.outer_sys.message.send_msg import SendMessage
from app.schema.equipment import 装备InResponse
from app.schema.robot import 机器人inResponse, 机器人附带分类
from app.service.datetime import get_early_morning
from app.service.publish.strategy_publish_log import 创建错误日志

AIRFLOW_EQUIPMENT_CODE = [装备分类转换.选股, 装备分类转换.择时, 装备分类转换.大类资产配置, 装备分类转换.基金定投]
AIRFLOW_EQUIPMENT_NAME = [装备分类_3.选股, 装备分类_3.择时, 装备分类_3.大类资产配置, 装备分类_3.基金定投]
DEFAULT_ROBOT_FILTER = {"状态": {"$in": ["已上线", "已下线"]}, "标识符": {"$regex": "^10"}}
DEFAULT_EQUIPMENT_FILTER = {"状态": {"$in": ["已上线", "已下线"]}, "分类": {"$in": AIRFLOW_EQUIPMENT_NAME}}


async def 策略标识符列表(conn: AsyncIOMotorClient, filters: dict = None):
    filters = filters or {}
    robot_filter = {}
    robot_filter.update(DEFAULT_ROBOT_FILTER)
    robot_filter.update(filters)
    equipment_filter = {}
    equipment_filter.update(DEFAULT_EQUIPMENT_FILTER)
    equipment_filter.update(filters)
    robot_sid_list = [x["标识符"] async for x in get_robots_collection(conn).find(robot_filter, {"标识符": 1})]
    equipment_sid_list = [x["标识符"] async for x in get_equipment_collection(conn).find(equipment_filter, {"标识符": 1})]
    return robot_sid_list + equipment_sid_list


async def write_strategy_publish_log_task(conn: AsyncIOMotorClient = None, tdate=None, username=None, send_email=True):
    conn = conn or db.client
    if not FastTdate.is_tdate():
        return None
    users = await get_manufacturer_user(db.client, username=username)
    insert_list = []
    tdate = tdate or get_early_morning(datetime.today())
    sid_list = await 策略标识符列表(conn)
    success_sid_list = await 策略标识符列表(conn, {"计算时间": tdate})
    failure_sid_list = await 策略标识符列表(conn, {"计算时间": {"$ne": tdate}})
    online_sid_list = await 策略标识符列表(conn, {"状态": "已上线"})
    offline_sid_list = await 策略标识符列表(conn, {"状态": "已下线"})

    for user in users:
        effective_robot = [x for x in user.client.robot if x.startswith("10")]
        effective_equipment = [x for x in user.client.equipment if x[:2] in AIRFLOW_EQUIPMENT_CODE]
        user_strategy_list = set(effective_robot + effective_equipment)
        总共发布策略数量 = len(user_strategy_list)
        当日发布策略数量 = len(set([x for x in sid_list if x in user_strategy_list]))
        报错策略数量 = len(set([x for x in failure_sid_list if x in user_strategy_list]))
        成功策略数量 = len(set([x for x in success_sid_list if x in user_strategy_list]))
        已上线策略数量 = len([x for x in online_sid_list if x in user_strategy_list])
        已下线策略数量 = len([x for x in offline_sid_list if x in user_strategy_list])
        是否完成发布 = True if 当日发布策略数量 == 总共发布策略数量 else False
        log = StrategyPublishLog(
            username=user.username,
            交易日期=tdate,
            总共发布策略数量=总共发布策略数量,
            当日发布策略数量=当日发布策略数量,
            报错策略数量=报错策略数量,
            成功策略数量=成功策略数量,
            已上线策略数量=已上线策略数量,
            已下线策略数量=已下线策略数量,
            是否完成发布=是否完成发布,
            错误策略=list(set([x for x in failure_sid_list if x in user_strategy_list])),
        )
        insert_list.append(InsertOne(log.dict()))
        if 是否完成发布:
            data = {
                "event": "update_cn_collection",
            }
            headers = {"username": user.username, "secret-key": user.app_secret}
            try:
                response = requests.post(f"{user.client.base_url}/jinniu/update_cn_collection", json=data, headers=headers)
                if not response.json().get("result") or response.json()["result"] != "success":
                    raise ValueError(str(response.json()))
            except Exception as e:
                logger.error(f"通知厂商用户发布数据失败({e}).")
                continue
    if insert_list:
        await get_strategy_publish_log_collection(db.client).bulk_write(insert_list)
    # 发送邮件
    if send_email:
        await 发送消息_策略最新发布情况(conn, tdate)


async def 回测评级验证(obj: Union[机器人inResponse, 装备InResponse]):
    collection_schema = "{}回测评级collection名"
    if obj.分类 == "择时":
        await 验证回测年份连续(collection_schema, obj, "回测评级")
        await 验证标的指数(collection_schema, obj, "回测评级")
    else:
        for 数据集 in 回测评级数据集:
            if not await get_collection_by_config(db.client, collection_schema.format(obj.分类)).find_one({"标识符": obj.标识符, "数据集": 数据集}):
                raise ValueError(f"[{obj.标识符}]回测评级.{obj.分类}数据不完整(缺少`{数据集}`数据集).")
    await 验证所有字段不为空(collection_schema, obj, "回测评级")


async def 回测指标验证(obj: Union[机器人inResponse, 装备InResponse]):
    collection_schema = "{}回测指标collection名"
    Range = namedtuple("Range", ["start", "end"])
    if obj.分类 == "选股":
        cursor = get_collection_by_config(db.client, collection_schema.format(obj.分类)).find({"标识符": obj.标识符})
        obj_list = [item async for item in cursor]
        if len(obj_list) != 3:
            raise ValueError(f"[{obj.标识符}]回测指标.{obj.分类}数据不完整.")
        for item in obj_list:
            if item["开始时间"] == item["结束时间"]:
                raise ValueError(f"[{obj.标识符}]回测指标.{obj.分类}数据不完整([{item['_id']}]开始时间和结束时间相等).")
        r1 = Range(start=obj_list[0]["开始时间"], end=obj_list[0]["结束时间"])
        r2 = Range(start=obj_list[1]["开始时间"], end=obj_list[1]["结束时间"])
        latest_start = max(r1.start, r2.start)
        earliest_end = min(r1.end, r2.end)
        delta = (earliest_end - latest_start).days + 1
        overlap = max(0, delta)
        if overlap < 0:
            raise ValueError(f"[{obj.标识符}]回测指标.{obj.分类}数据不完整(时间段重叠).")

    elif obj.分类 == "择时":
        await 验证回测年份连续(collection_schema, obj, "回测指标")
        await 验证标的指数(collection_schema, obj, "回测指标")
    else:
        await 验证连续交易日(collection_schema, obj, "回测指标", end=obj.上线时间)
    await 验证所有字段不为空(collection_schema, obj, "回测指标")


async def 回测信号验证(obj: Union[机器人inResponse, 装备InResponse]):
    collection_schema = "{}回测信号collection名"
    if obj.分类 == "选股":
        await 验证连续交易日(collection_schema, obj, "回测信号", end=obj.上线时间)
    elif obj.分类 == "择时":
        await 验证连续交易日(collection_schema, obj, "回测信号", end=obj.上线时间)
        await 验证标的指数(collection_schema, obj, "回测信号")
    else:
        await 验证连续交易日(collection_schema, obj, "回测信号", end=obj.上线时间)
    await 验证所有字段不为空(collection_schema, obj, "回测信号")


async def 实盘信号验证(obj: Union[机器人inResponse, 装备InResponse]):
    collection_schema = "{}实盘信号collection名"
    if obj.分类 == "选股":
        await 验证连续交易日(collection_schema, obj, "实盘信号", start=obj.上线时间, end=obj.计算时间)
    elif obj.分类 == "择时":
        await 验证连续交易日(collection_schema, obj, "实盘信号", start=obj.上线时间, end=obj.计算时间)
        await 验证标的指数(collection_schema, obj, "实盘信号")
    else:
        await 验证连续交易日(collection_schema, obj, "实盘信号", start=obj.上线时间, end=obj.计算时间)
    await 验证所有字段不为空(collection_schema, obj, "实盘信号")


async def 实盘指标验证(obj: Union[机器人inResponse, 装备InResponse]):
    collection_schema = "{}实盘指标collection名"
    if obj.分类 == "基金定投" or obj.分类 == "大类资产配置" or obj.分类 == "机器人":
        await 验证连续交易日(collection_schema, obj, "实盘指标", start=obj.上线时间, end=obj.计算时间)
        await 验证所有字段不为空(collection_schema, obj, "实盘指标")


async def 验证所有字段不为空(collection_schema: str, obj: Union[机器人inResponse, 装备InResponse], type_: str):
    cursor = get_collection_by_config(db.client, collection_schema.format(obj.分类)).find({"标识符": obj.标识符})
    async for item in cursor:
        for k, v in item.items():
            if v is None:
                raise ValueError(f"[{obj.标识符}]{type_}.{obj.分类}数据不完整(字段`{k}`的值为空).")


async def 验证回测年份连续(collection_schema: str, obj: Union[机器人inResponse, 装备InResponse], type_: str):
    cursor = get_collection_by_config(db.client, collection_schema.format(obj.分类)).find({"标识符": obj.标识符})
    d = defaultdict(list)
    async for item in cursor:
        d[item["标的指数"]].append(item["回测年份"])
    for symbol, year_list in d.items():
        if "全部" not in year_list:
            raise ValueError(f"[{obj.标识符}]{type_}.{obj.分类}数据不完整(缺少标的指数{symbol}回测年份`全部`的数据).")
        year_list.sort()
        for index, year in enumerate(year_list[:-2]):
            if int(year) + 1 != int(year_list[index + 1]):
                raise ValueError(f"[{obj.标识符}]{type_}.{obj.分类}数据不完整(缺少标的指数{symbol}回测年份`{year}`的数据).")


async def 验证标的指数(collection_schema: str, obj: Union[机器人inResponse, 装备InResponse], type_: str):
    标的指数列表 = ["000001", "000300", "000905", "399001", "399006"]
    for 标的指数 in 标的指数列表:
        cursor = get_collection_by_config(db.client, collection_schema.format(obj.分类)).find({"标识符": obj.标识符, "标的指数": 标的指数})
        if not cursor:
            raise ValueError(f"[{obj.标识符}]{type_}.{obj.分类}数据不完整(缺少`{标的指数}`标的指数).")


async def 验证连续交易日(
    collection_schema: str,
    obj: Union[机器人inResponse, 装备InResponse],
    type_: str,
    *,
    end: datetime,
    start: datetime = datetime.strptime("20140101", "%Y%m%d"),
):
    cursor = get_collection_by_config(db.client, collection_schema.format(obj.分类)).find({"标识符": obj.标识符})
    obj_tdate_list = [item["交易日期"] async for item in cursor if item]
    if not obj_tdate_list:
        raise ValueError(f"[{obj.标识符}]{type_}.{obj.分类}数据不完整(缺少数据).")
    obj_tdate_list = list(set(obj_tdate_list))
    obj_tdate_list.sort()
    all_tdate_list = FastTdate.query_all_tdates(start, end)
    if len(obj_tdate_list) != len(all_tdate_list):
        raise ValueError(f"[{obj.标识符}]{type_}.{obj.分类}数据不完整(缺少`{abs(len(obj_tdate_list)-len(all_tdate_list))}" f"`个交易日的数据).")
    for obj_tdate, all_tdate in zip(obj_tdate_list, all_tdate_list):
        if str(obj_tdate) != str(all_tdate):
            raise ValueError(f"[{obj.标识符}]{type_}.{obj.分类}数据不完整(缺少交易日期`{all_tdate}`的数据).")


async def check_strategy_data_task(tdate=None, sid=None):
    """检查策略数据任务."""
    if not FastTdate.is_tdate():
        return None
    try:
        robot_filter = {"状态": {"$in": ["已上线", "已下线"]}, "标识符": {"$regex": "^10"}}
        robot_filter.update({"标识符": [sid]}) if sid else None
        robot_list = await 查询机器人列表(db.client, robot_filter, limit=0, skip=0)
        equipment_filter = {"状态": {"$in": ["已上线", "已下线"]}, "分类": {"$in": AIRFLOW_EQUIPMENT_NAME}}
        equipment_filter.update({"标识符": [sid]}) if sid else None
        equipment_list = await 查询装备列表(db.client, equipment_filter, limit=0, skip=0, 排序=[("交易日期", 1)])
    except NoUserError:
        logger.error("检查策略数据任务执行失败, 查询机器人或装备列表错误(未找到装备或机器人的作者).")
        return None
    except Exception as e:
        logger.error(f"{e}.")
        return None
    tdate = tdate or get_early_morning(datetime.today())
    robot_list = [机器人附带分类(**obj.dict()) for obj in robot_list]
    for obj in robot_list + equipment_list:
        if not hasattr(obj, "分类"):
            obj.分类 = "机器人"
        if obj.分类 not in ["机器人", "选股", "基金定投", "择时", "大类资产配置"]:
            continue
        try:
            await 回测评级验证(obj)
            await 回测指标验证(obj)
            await 回测信号验证(obj)
            await 实盘信号验证(obj)
            await 实盘指标验证(obj)
        except ValueError as e:
            await 创建错误日志(db.client, obj.分类, str(e), str(e), obj.标识符, tdate, 错误信息错误类型enum.缺失策略)


async def 发送消息_策略最新发布情况(conn: AsyncIOMotorClient, tdate):
    success_sid_list = await 策略标识符列表(conn, {"计算时间": tdate})
    failure_sid_list = await 策略标识符列表(conn, {"计算时间": {"$ne": tdate}})
    total = pd.DataFrame(
        {
            "总共发布策略数量": len(success_sid_list) + len(failure_sid_list),
            "报错策略数量": len(failure_sid_list),
            "成功策略数量": len(success_sid_list),
        },
        index=[0],
    )
    res_list = []
    idx_val = 0
    for idx, sid in enumerate(success_sid_list):
        res_list.append(
            pd.DataFrame(
                {
                    "分类": "机器人" if sid.startswith("10") else 装备分类转换.__dict__["_value2member_map_"][sid[:2]].name,
                    "标识符": sid,
                    "今日数据": "已完成",
                },
                index=[idx_val + idx],
            )
        )
    for idx, sid in enumerate(failure_sid_list):
        res_list.append(
            pd.DataFrame(
                {
                    "分类": "机器人" if sid.startswith("10") else 装备分类转换.__dict__["_value2member_map_"][sid[:2]].name,
                    "标识符": sid,
                    "今日数据": "未完成",
                },
                index=[idx_val + len(success_sid_list) + idx],
            )
        )
    content = pd.concat(res_list)
    content = content.sort_values("分类").reset_index(drop=True)
    sm = SendMessage(SendEmail())
    params = {
        "to_addr": settings.airflow.emails,
        "title": f"智道-策略发布情况 {tdate:%Y-%m-%d}",
        "content": total.to_html() + "<br>" * 3 + content.to_html(),
        "send_type": "html",
    }
    try:
        sm.send(**params)
    except SMTPResponseException as e:
        logger.error(f"Code:{e.smtp_code} Msg:{e.smtp_error.decode()}")
    except Exception as e:
        logger.error(f"消息发送失败！失败详情；{e}")
    else:
        return True
