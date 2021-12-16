from functools import lru_cache


@lru_cache()
def convert_exchange(exchange: str, to: str) -> str:
    """转换交易市场格式.

    输入任意格式股票市场，输出特定格式股票市场
    输出类型可选值为: `stralib` `beehive` `hq`
    """
    format_mapping = {"stralib": 0, "beehive": 1, "hq": 2}
    if to not in format_mapping.keys():
        raise ValueError(f"未定义市场格式`{to}`.")
    CNSESH = ["CNSESH", "1", "SH"]
    CNSESZ = ["CNSESZ", "0", "SZ"]
    if exchange not in CNSESH and exchange not in CNSESZ:
        raise ValueError(f"未找到`{exchange}`市场.")
    if exchange in CNSESH:
        return CNSESH[format_mapping[to]]
    if exchange in CNSESZ:
        return CNSESZ[format_mapping[to]]
