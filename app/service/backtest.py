import copy
import logging
from datetime import datetime
from typing import Union

from stralib import get_config, FastTdate, SysConfig, RobotMatchUp, UserConfig
from stralib.data_service.client import DataClient
from stralib.data_service.robot_data import RobotData
from stralib.models.robot import 机器人

from app.outer_sys.hq import get_security_info

try:
    from stralib.robot import *
except ImportError:
    pass

from app.crud.robot import get_robot
from app.service.str.styles import to_underline_dict, to_hump_dict


def init_start(data, logger):
    """初始化start参数"""
    total_trade_date = FastTdate.query_all_tdates(data["start"], data["end"], include_stop=True)
    data["tdate_num"] = len(total_trade_date)
    real_start = total_trade_date[0] if len(total_trade_date) else ""
    real_end = total_trade_date[-1] if len(total_trade_date) else ""
    data["real_end"] = real_end
    data["real_start"] = real_start
    user_config = {
        "fundbal": int(data.get("fund_available", 500000) or 500000),
        "mktval": int(data.get("market_value", 0) or 0),
        "stocks": data.get("position", []),
        "max_hold_day": int(data["adjust_cycle"]),
        "max_hold_num": int(data["max_quantity"]),
        "last_signals": data.get("modified_orders", []),
        "run_type": "backtest",
    }
    data["user_config"] = user_config
    logger.info(f"total_trade_date {total_trade_date}")


def get_sys_config(beehive_robot: 机器人, start: str, end: str):
    start = datetime.strptime(start, "%Y%m%d")
    end = datetime.strptime(end, "%Y%m%d")
    sys_config = SysConfig(
        start_date=FastTdate.last_tdate(start),
        end_date=end,
        all_risk_sid_list=beehive_robot.风控装备列表,
        all_timing_sid_list=beehive_robot.择时装备列表,
        all_stock_sid_list=beehive_robot.选股装备列表,
        all_tstock_tsid_list=beehive_robot.交易装备列表,
    )
    return sys_config


def get_user_config(beehive_robot: 机器人, start: Union[str, datetime], end: Union[str, datetime]):
    user_config = UserConfig.generate_userconfig(start, end, beehive_robot, run_type="backtest")
    return user_config


def get_robot_data(beehive_robot: 机器人, start: str, end: str, from_ds=True):
    sysconfig = get_sys_config(beehive_robot, start, end)
    if from_ds:
        store_name = get_config("DATA_SERVICE_NAME")
        try:
            client = DataClient(store_name)
            robot_contain = client.contains(beehive_robot.标识符)
        except Exception as e:
            logging.warning(f"[获取data service 数据异常]{e}")
            robot_data = RobotData(sysconfig)
        else:
            if robot_contain:
                robot_data = client.get_robot_data(beehive_robot.标识符, FastTdate.last_tdate(sysconfig.start_date), sysconfig.end_date)
            else:
                robot_data = RobotData(sysconfig)
    else:
        robot_data = RobotData(sysconfig)
    return robot_data


def get_robot_match_up(beehive_robot: 机器人, start: str, end: str, asset: dict = None, stocks: list = None):
    asset = asset or {"fundbal": 500000, "mktval": 0}
    stocks = stocks or []
    user_config = get_user_config(beehive_robot, start, end)
    robot_data = get_robot_data(beehive_robot, start, end)
    ret_data = RobotMatchUp(asset, stocks, user_config, robot_data)
    return ret_data


def update_user_config(result, user_config):
    """更新入参"""
    user_config["fundbal"] = result["account_data"]["total_fund"] - result["account_data"]["position"]["market_value"]
    user_config["mktval"] = result["account_data"]["position"]["market_value"]
    user_config["stocks"] = result["account_data"]["position"]["stocks"] or []
    if result["orders_proposed"]:
        user_config["last_signals"] = result["orders_proposed"]
    else:
        user_config["last_signals"] = []


async def format_signal(order, stocks=None):
    security = await get_security_info(order["SYMBOL"], order["MARKET"])
    ret_data = {
        "交易所": order["MARKET"],
        "股票代码": order["SYMBOL"],
        "股票名称": security.symbol_name,
        "交易方向": order["SIGNAL"],
        "交易数量": order["STKEFFEFT"],
        "价格": order["TPRICE"],
    }
    if order["SIGNAL"] == 1 and stocks:
        ret_data["成交价"] = [x["avg_price"] for x in stocks if order["SYMBOL"] == x["symbol"]][0]
        ret_data["收益率"] = order["TPRICE"] / ret_data["成交价"] - 1
    return ret_data


def format_order(order, asset):
    ret_data = {
        "交易所": order["market"],
        "数量": order["stkbal"],
        "股票代码": order["symbol"],
        "股票名称": order["sname"],
        "现价": order["tprice"],
        "成本价": order["avg_price"],
        "市值": order["mktval"],
        "仓位": round(order["mktval"] / sum(asset.values()), 4),
        "收益率": round(order["mktval"] / sum(asset.values()), 4),
    }
    return ret_data


def format_回测数据(tdate, data):
    ret_data = {
        "交易日期": datetime.strftime(tdate, "%Y%m%d"),
        "可用资金": data["asset"]["fundbal"],
        "当前市值": data["asset"]["mktval"],
        "当前持仓": [format_order(x, data["asset"]) for x in data["stocks"]],
        "当日成交订单": [format_signal(x, data["stocks"]) for x in data["signals"]],
        "当日信号": [format_signal(x) for x in data["last_signals"]],
        "初始资金": 500000.0,
        "总资产": sum(data["asset"].values()),
        "总收益率": sum(data["asset"].values()) / 500000 - 1,
    }
    return ret_data


async def 初始化回测数据(websocket, logger=logging):
    data = await websocket.receive_json()
    json_data = to_underline_dict(data)
    data = json_data["data"]
    init_start(data, logger)
    ret_data = {"event": "start_callback", "data": to_hump_dict(data)}
    await websocket.send_json(ret_data)


async def 获取回测数据(websocket, db):
    data = await websocket.receive_json()
    json_data = to_underline_dict(data)
    data = json_data["data"]
    user_config = data["user_config"]
    is_auto = data["is_auto"]
    robot = await get_robot(data["robot_id"], db)
    fundbal = int(user_config.pop("fund_available", 500000))
    mktval = int(user_config.pop("market_value", 0) or 0)
    asset = {"fundbal": fundbal, "mktval": mktval}
    stocks = user_config.pop("stocks", []) or []
    for stock in stocks:
        stock["stopup"] = 99999999
        stock["stopdown"] = 0
    userconfig_obj = get_user_config(robot, data["start"], data["end"])
    robot_data = get_robot_data(robot, data["start"], data["end"])
    robot_match_up = RobotMatchUp(asset, stocks, userconfig_obj, robot_data)
    try:
        for item in robot_match_up.robot_yield_trader():
            tmp = tuple(item.items())[0]
            result = format_回测数据(tmp[0], copy.deepcopy(tmp[1]))
            ret_data = {"event": "backtest_data", "data": result}
            await websocket.send_json(ret_data)
            if not is_auto and result["当日信号"]:
                break
    except Exception as e:
        logging.warning(f"backtest_next[结束] {e}", exc_info=True)
        await websocket.send_json({"event": "end"})
