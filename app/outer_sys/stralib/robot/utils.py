from typing import List, Dict, Any

from app.outer_sys.hq import get_security_info
from app.utils.data_format import name_mapping

signal_key_mapping = {
    "symbol": "SYMBOL",
    "exchange": "MARKET",
    "quantity": "STKEFFEFT",
    "date": "TDATE",
    "operator": "SIGNAL",
    "reason": "OPERATOR",
    "price": "TPRICE",
}

database_stock_key_mapping = {
    "exchange": "market",
    "market_value": "mktval",
    "stop_loss": "stopdown",
    "stop_profit": "stopup",
    "stock_quantity": "stkbal",
}


db2robot_position_mapping = {"exchange": "market", "current_price": "tprice", "volume": "stkbal"}


def principle_to_robot(principle):
    """将组合中的原则字段转换为机器人中的格式"""
    return {"max_hold_day": principle.adjust_cycle, "max_hold_num": principle.max_quantity}


def signal_list_to_robot(signal_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将API接口中的信号数据转换为机器人中的格式"""
    for signal in signal_list:
        signal_to_robot(signal)
    return signal_list


def signal_to_robot(signal: Dict[str, Any]) -> Dict[str, Any]:
    signal_batch_format(signal, reverse=True)
    name_mapping(signal_key_mapping, signal, reverse=True)
    return signal


def signal_batch_format(*signals, reverse=False):
    """
    将 signal 格式的字典格式化
    Parameters
    ----------
    signals:    多个 signal
    reverse:    True 表示从接口层格式到服务层格式, False 表示从服务层格式到接口层格式
    """
    for signal in signals:
        exchange_format(signal, reverse=reverse)
        operator_format(signal, reverse=reverse)
        reason_format(signal, reverse=reverse)


def exchange_format(item, key="exchange", reverse=False):
    mapping = {"CNSESH": "1", "CNSESZ": "0"}
    if reverse:
        mapping = {key: value for value, key in mapping.items()}
    item[key] = mapping[item.pop(key)]


def operator_format(item, key="operator", reverse=False):
    mapping = {1: "buy", -1: "sell"}
    if reverse:
        mapping = {key: value for value, key in mapping.items()}
    item[key] = mapping[item.pop(key)]


def reason_format(item, key="reason", reverse=False):
    value = item.pop(key)
    try:
        if not reverse:
            item[key] = str(int(value))
        else:
            item[key] = int(value) if value.isdigit() else value
    except Exception:
        item[key] = value


async def signal_list_to_api(signal_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将机器人中的信号数据转换为 api 接口中的格式"""
    for signal in signal_list:
        await signal_to_api(signal)
    return signal_list


async def signal_to_api(signal: Dict[str, Any]) -> Dict[str, Any]:
    name_mapping(signal_key_mapping, signal, reverse=False)
    signal_batch_format(signal)
    # 添加股票名到order
    stock_info = await get_security_info(signal["symbol"], signal["exchange"])
    signal["symbol_name"] = stock_info.symbol_name
    return signal
