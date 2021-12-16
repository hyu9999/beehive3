"""
维护redis内的股票池，提供实时股票行情
"""
import re
from typing import Dict, List

from app.outer_sys.hq import get_security_info


async def fill_description(position: List[Dict[str, str]]) -> List:
    """
    向原始数据填充股票的详细信息，包括行业和股票名等信息
    :param position: 持仓列表
    :return: 填充了详细信息后的持仓列表
    """
    descriptions = []
    for item in position:
        security = await get_security_info(item["symbol"], item["exchange"])
        data = security.dict()
        data["exchange"] = "1" if security.exchange == "SH" else "0"
        descriptions.append(data)
    for to_fill, data in zip(position, descriptions):
        to_fill.update(data)
    return position
