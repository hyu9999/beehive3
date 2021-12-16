from typing import List, Dict

import requests
from cacheout import Cache

from app import settings
from app.enums.equipment import 装备分类转换
from app.models.equipment import (
    选股装备回测评级,
    择时装备回测评级,
    大类资产配置回测评级,
    基金定投回测评级,
    选股装备回测指标,
    择时装备回测指标,
    大类资产配置回测指标,
    基金定投回测指标,
    选股装备回测信号,
    择时装备回测信号,
    大类资产配置回测信号,
    基金定投回测信号,
)
from app.models.robot import 机器人回测评级, 机器人回测指标, 机器人回测信号

cache = Cache()

CN_DATA_TYPE_CONVERSION = {"实盘信号": "real_signal", "实盘指标": "real_indicator", "回测信号": "backtest_signal", "回测指标": "backtest_indicator", "回测评级": "backtest_assess"}
BACKTEST_DATA_TYPE_CONVERSION = {
    "回测评级.选股装备": 选股装备回测评级,
    "回测评级.机器人": 机器人回测评级,
    "回测评级.择时装备": 择时装备回测评级,
    "回测评级.大类资产配置": 大类资产配置回测评级,
    "回测评级.基金定投": 基金定投回测评级,
    "回测指标.选股装备": 选股装备回测指标,
    "回测指标.机器人": 机器人回测指标,
    "回测指标.择时装备": 择时装备回测指标,
    "回测指标.大类资产配置": 大类资产配置回测指标,
    "回测指标.基金定投": 基金定投回测指标,
    "回测信号.选股装备": 选股装备回测信号,
    "回测信号.机器人": 机器人回测信号,
    "回测信号.择时装备": 择时装备回测信号,
    "回测信号.大类资产配置": 大类资产配置回测信号,
    "回测信号.基金定投": 基金定投回测信号,
}


@cache.memoize(ttl=3600 * 24, typed=True)
def jinniu_token() -> dict:
    data = {"user": {"mobile": settings.mfrs.CLIENT_USER, "app_secret": settings.mfrs.APP_SECRET}}
    result = requests.post(f"{settings.mfrs.BEEHIVE_URL}/auth/login", json=data)
    return {"Authorization": "Token " + result.json().get("token")}


class Beehive:
    def __init__(self):
        self.header = jinniu_token()

    def get_routes_params_from_collection(self, table_name: str):
        """根据集合名称获取格式化后的路由参数"""
        params_type = "robots" if table_name.startswith("机器人", 5) else "equipment"
        data_type = CN_DATA_TYPE_CONVERSION[table_name[:4]]
        return params_type, data_type

    def filter_sid(self, table_name: str, sid_list: list):
        """过滤sid"""
        sid_list = [x for x in sid_list if not x.startswith("15")]
        if table_name.startswith("选股", 5):
            sid_list = [x for x in sid_list if x.startswith(装备分类转换.选股.value)]
        if table_name.startswith("择时", 5):
            sid_list = [x for x in sid_list if x.startswith(装备分类转换.择时.value)]
        if table_name.startswith("大类资产配置", 5):
            sid_list = [x for x in sid_list if x.startswith(装备分类转换.大类资产配置.value)]
        if table_name.startswith("基金定投", 5):
            sid_list = [x for x in sid_list if x.startswith(装备分类转换.基金定投.value)]
        if table_name.startswith("机器人", 5):
            sid_list = [x for x in sid_list if x.startswith("10")]
        return sid_list

    def get_cn_data_from_beehive(self, params_type: str, data_type: str, sid: str, params: dict = None) -> list:
        """根据指定的params条件获取全部实盘数据"""
        data = []
        skip, limit = 0, 10000
        while True:
            # 循环获取，目的获取限定条件内全部数据
            params.update({"skip": skip, "limit": limit})
            resp = requests.get(f"{settings.mfrs.BEEHIVE_URL}/{params_type}/{sid}/{data_type}", params=params, headers=self.header)
            if resp.status_code == 200:
                if resp.json():
                    # 中文表接口返回数据均为list，如类型有变更，则extend需变更
                    data.extend(resp.json())
                    skip += limit
                else:
                    break
            else:
                break
        return data

    def format_response(self, format_type, data_list) -> list:
        """利用模型格式化响应数据，返回格式化后的数据"""
        result = [format_type(**data).dict(by_alias=True) for data in data_list]
        return result

    def query_cn_data(self, table_name: str, params_list: List[Dict[str, str]]) -> list:
        """从beehive获取中文表数据，过滤响应为400数据，合并数据为列表"""
        params_type, data_type = self.get_routes_params_from_collection(table_name)
        data = []
        for params in params_list:
            resp = self.get_cn_data_from_beehive(params_type, data_type, params["sid"], params={"start": params["start"], "end": params["end"]})
            data.extend(resp)
        return data

    def query_backtest_data(self, table_name: str, sid_list: list, params: dict = None) -> list:
        """从beehive获取回测列表数据"""
        params_type, data_type = self.get_routes_params_from_collection(table_name)
        sid_list = self.filter_sid(table_name, sid_list)
        data = []
        format_type = BACKTEST_DATA_TYPE_CONVERSION[table_name]
        for sid in sid_list:
            # 查询择时装备的回测评级与回测指标数据时，symbol默认参数为399001，需循环传入指数列表，获取全部数据
            if sid.startswith(装备分类转换.择时.value) and data_type in ["backtest_indicator", "backtest_assess"]:
                for symbol in ["000300", "399001", "000001", "000905", "399006"]:
                    resp = self.get_cn_data_from_beehive(params_type, data_type, sid, {"symbol": symbol})
                    data.extend(self.format_response(format_type, resp))
            else:
                resp = self.get_cn_data_from_beehive(params_type, data_type, sid, params)
                data.extend(self.format_response(format_type, resp))
        return data

    def query_robot_or_equipment_info(self, table_name: str, sid: str):
        resp = requests.get(f"{settings.mfrs.BEEHIVE_URL}/{table_name}/{sid}", headers=self.header).json()
        return resp
