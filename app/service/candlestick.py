from abc import ABCMeta, abstractmethod
from datetime import date
from typing import Union

from pandas import DataFrame
from stralib import FastTdate, get_series_data
from zvt.domain import Stock1dBfqKdata, Index1dKdata

from app import settings
from app.data_map.stock import SERIES_DATA_MAP, SYMBOL_NAME_MAP


class KDataSource(metaclass=ABCMeta):
    @abstractmethod
    def stock(self, *args, **kwargs):
        """股票K线图"""

    @abstractmethod
    def market(self, *args, **kwargs):
        """市场指数k线图"""


class TongLianSource(KDataSource):
    """通联数据源"""

    def __init__(self, **kwargs):
        self.symbol = kwargs["symbol"]
        if "exchange" in kwargs.keys():
            self.symbol_name = kwargs["symbol_name"]
        else:
            self.symbol_name = SYMBOL_NAME_MAP[self.symbol]

    def stock(self, start_date, stop_date):
        """股票K线图"""
        if not FastTdate.query_all_tdates(start_date, stop_date, include_stop=True):
            return []
        data = self.get_base_data("CHDQUOTE", start_date, stop_date)
        return data

    def market(self, start_date, stop_date):
        """市场指数k线图"""
        if not FastTdate.query_all_tdates(start_date, stop_date, include_stop=True):
            return []
        data = self.get_base_data("CIHDQUOTE_SELECTED", start_date, stop_date)
        return data

    def get_base_data(self, table_name, start_date, stop_date):
        """获取基础数据"""
        df_all = get_series_data(table_name, start_date.strftime("%Y%m%d"), stop_date.strftime("%Y%m%d"))
        df = df_all[df_all.SNAME.isin([self.symbol_name])][["TOPEN", "HIGH", "LOW", "TCLOSE", "VOTURNOVER"]]
        df.rename(columns=SERIES_DATA_MAP, inplace=True)
        data = []
        for k, v in df.T.to_dict().items():
            tmp_dict = {"时间戳": k[0].strftime("%Y-%m-%d")}
            tmp_dict.update(v)
            data.append(tmp_dict)
        return data


class ZVTSource(KDataSource):
    """zvt数据源"""

    def __init__(self, **kwargs):
        self.symbol = kwargs["symbol"]

    def _base(self, table_obj: Union[Stock1dBfqKdata, Index1dKdata], start_date: date, stop_date: date):
        if not FastTdate.query_all_tdates(start_date, stop_date, include_stop=True):
            return []
        data = table_obj.query_data(
            code=self.symbol,
            start_timestamp=f"{start_date:%Y-%m-%d} 00:00:00",
            end_timestamp=f"{stop_date:%Y-%m-%d} 00:00:00",
            columns=[
                table_obj.timestamp,
                table_obj.open,
                table_obj.high,
                table_obj.low,
                table_obj.close,
                table_obj.volume,
            ],
        )
        return self.format_data(data)

    def stock(self, start_date: date, stop_date: date):
        """股票K线图"""
        return self._base(Stock1dBfqKdata, start_date, stop_date)

    def market(self, start_date: date, stop_date: date):
        """市场指数k线图"""
        return self._base(Index1dKdata, start_date, stop_date)

    @staticmethod
    def format_data(data: DataFrame):
        data["timestamp"] = data["timestamp"].apply(lambda x: x.strftime("%Y-%m-%d"))
        data = data.rename(columns={"timestamp": "时间戳", "open": "开盘价", "high": "最高价", "low": "最低价", "close": "收盘价", "volume": "成交量"})
        data = data.round(2)  # 小数保留两位
        return data.to_dict("records")


class KDataDiagram:
    source_map = {"tonglian": TongLianSource, "zvt": ZVTSource}

    def __init__(self, **kwargs):
        if settings.manufacturer_switch:
            source = "tonglian"
        else:
            source = "zvt"
        self.source = self.source_map[source](**kwargs)

    def stock(self, start_date: date, stop_date: date):
        """股票K线图"""
        return self.source.stock(start_date, stop_date)

    def market(self, start_date: date, stop_date: date):
        """市场指数k线图"""
        return self.source.market(start_date, stop_date)
