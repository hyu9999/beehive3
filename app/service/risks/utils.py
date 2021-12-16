from app.enums.portfolio import 风险类型


# 组合装备给给出的风险类型到 beehive 的风险类型
# key 的字段属于组合装备, value 的字段属于 beehive 的风险类型
operator_risk_type_mapping = {
    8: "12",
    5: "10",
    6: "0",
    7: "1",
    9: "9",
    10: "8",
    11: "8",
    "dqzs01": "3",
    "kthq01": "7",
    "pst001": "6",
    "sjyj01": "2",
    "st0001": "5",
    "yxfz01": "4"
}


def risk_type_from_signal(signal, key="OPERATOR"):
    """获取信号的风险类型"""
    op = signal[key]
    mapping_key = op if isinstance(op, str) else int(op)
    return operator_risk_type_mapping.get(mapping_key, None)


def is_stock_signal(signal):
    """判断给定信号是否为个股风险信号"""
    risk_type = risk_type_from_signal(signal)
    if not risk_type or risk_type in (风险类型.overweight, 风险类型.underweight):
        return False
    else:
        return True


async def select_stock_signals(signals):
    """筛选出 signals 中属于个股风险的信号, 排除交易信号"""
    return list(filter(is_stock_signal, signals))


async def get_exchange_from_signal(signal, key='MARKET'):
    """从风险信号获取交易所代码"""
    return "0" if signal.get(key) == "CNSESZ" else "1"