import re
from collections import OrderedDict
from typing import Any, Dict, List

from app.enums.solution import SolutionStepEnum

TITLE_LIST = {
    "0": "",
    "1": "清仓线风险的解决方案",
    "2": "止盈止损、调仓周期、个股风险的解决方案",
    "3": "仓位过轻的解决方案",
    "4": "仓位过重的解决方案",
    "5": "确认买入新股票",
    "6": "最终解决方案",
}
AIMS_LIST = {
    "0": "",
    "1": "解决清仓线风险",
    "2": "解决个股风险",
    "3": "解决仓位风险",
    "4": "解决仓位风险",
    "5": "确认买入新股票",
    "6": "点击完成，忽略所有风险",
}


def market_from_symbol(symbol: str) -> str:
    """根据股票代码返回对应交易所代码"""
    sz_pattern = r"\A(00)|(3)|(20)|(080)|(031)|(50)|(51)|(52)"
    sh_pattern = r"\A(6)|(900)|(730)|(700)|(580)|(15)|(16)|(18)"
    if re.match(sh_pattern, symbol):
        return "1"
    elif re.match(sz_pattern, symbol):
        return "0"
    else:
        raise Exception(f"未知的股票代码模式: {symbol}")


async def fmt_rsp_msg(
    solution_type: SolutionStepEnum = None,
    solutions: List[Dict[str, Any]] = None,
    description: str = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Parameters
    ----------
    solution_type   解决方案类型
    solutions       具体解决方案
    description     描述
    """
    title = TITLE_LIST.get(str(solution_type.value))
    aims = AIMS_LIST.get(str(solution_type.value))
    solution_type = solution_type or SolutionStepEnum.START_FLAG
    solutions = solutions or []
    description = description or "没有风险点, 无需解决方案"
    ret_msg = OrderedDict()
    ret_msg["title"] = title
    ret_msg["aims"] = [aims]
    ret_msg["step"] = solution_type
    ret_msg["solutions"] = solutions
    ret_msg["status"] = description
    ret_msg.update(kwargs)
    return ret_msg
