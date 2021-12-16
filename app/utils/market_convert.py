from typing import Union


class MarketConverter:
    SZ = 0  # 深证
    SH = 1  # 上证

    STRALIB_EXCHANGE_MAPPER = {"CNSESZ": "0", "CNSESH": "1", "": "2", "XSHG": "1", "XSHE": "0"}

    def get_sys_market(self):
        """返回系统的市场id标准字典"""
        return {"SZ": self.SZ, "SH": self.SH}

    @classmethod
    def jiantou(cls, market_id: Union[int, str], reverse: bool = False):
        """
        建投市场id标准化：深证: 2，上证: 1

        Parameters
        ----------
        market_id: 市场代码
        reverse: 反转

        Returns
        -------
        new_market_id: 新的市场代码
        """
        market_id = market_id if isinstance(market_id, int) else int(market_id)
        if reverse:
            new_market = market_id if market_id == 1 else 2
        else:
            new_market = market_id if market_id == 1 else 0
        return new_market

    @classmethod
    def jq_data(cls, market_id: Union[int, str], reverse: bool = False):
        """
       聚宽市场id标准化：上证：XSHG，深证：XSHE

        Parameters
        ----------
        market_id: 市场代码
        reverse: 反转

        Returns
        -------
        new_market_id: 新的市场代码
        """
        if reverse:
            market_id = market_id if isinstance(market_id, int) else int(market_id)
            new_market = "XSHG" if market_id == 1 else "XSHE"
        else:
            new_market = 1 if market_id == "XSHG" else 0
        return new_market

    @classmethod
    def stralib(cls, market_id: Union[int, str], reverse: bool = False):
        """
        stralib市场id标准化：深证: CNSESZ/XSHE，上证: CNSESH/XSHG

        Parameters
        ----------
        market_id: 市场代码
        reverse: 反转

        Returns
        -------
        new_market_id: 新的市场代码
        """
        if reverse:
            market_id = market_id if isinstance(market_id, int) else int(market_id)
            new_market = "CNSESH" if market_id == 1 else "CNSESZ"
        else:
            new_market = 1 if market_id in ["CNSESH", "XSHG"] else 0
        return new_market
