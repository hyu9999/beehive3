import inspect
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientOSError, ClientResponseError, ServerDisconnectedError
from aiohttp.client import _RequestContextManager
from yarl import URL

from app.outer_sys.hq import get_security_info
from app.outer_sys.trade_system.pt import mapper
from app.outer_sys.trade_system.pt.mapper import EXCHANGE, ORDER_STATUS
from app.outer_sys.trade_system.trade_interface import TradeSystemAdaptor
from app.schema.trade_system import TradeInResponse


class PTAdaptor(TradeSystemAdaptor):
    """模拟交易适配."""

    def __init__(self, base_url: URL):
        TradeSystemAdaptor.__init__(self)
        self._base_url = base_url
        self._client = aiohttp.ClientSession(raise_for_status=True)

    def _make_url(self, path: str, name: str = "", query: Optional[dict] = None) -> URL:
        query_str = urlencode(query) if query is not None else ""
        return URL(f"{self._base_url}/{path}{name}?{query_str}")

    @staticmethod
    def _make_headers(login_required: bool = False, payload: Optional[dict] = None):
        headers = (
            {"Authorization": f"Token {payload.pop('account_id')}"}
            if login_required
            else None
        )
        return headers

    @staticmethod
    def out2beehive(func_name, data) -> dict:
        field_list = mapper.OUTPUT[func_name]
        rv = {}
        for beehive_field, out_field, default_value in field_list:
            out_value = data.get(out_field)
            rv[beehive_field] = out_value or default_value
        return rv

    @staticmethod
    def beehive2out(**kwargs) -> dict:
        rv = {}
        for item in kwargs:
            rv[mapper.INPUT[item]] = kwargs[item]
        return rv

    @staticmethod
    def function2interface(func_name: str) -> dict:
        return mapper.INTERFACE[func_name]

    @staticmethod
    def beehive_date_to_pt_date(date: str) -> str:
        try:
            return str(datetime.strptime(date, "%Y%m%d").date())
        except ValueError as e:
            raise ValueError(f"无法解析日期{date}。") from e

    def request_wrapper(
        self, method: str, url: URL, header: Optional[dict], json: Optional[dict]
    ) -> _RequestContextManager:
        if method == "POST":
            return self._client.request(method, url, headers=header, json=json)
        else:
            return self._client.request(method, url, headers=header)

    async def request_interface(
        self,
        func_name: str,
        payload: Optional[dict] = None,
        name: str = "",
        query: Optional[dict] = None,
        login_required: bool = True,
        convert_out: bool = True,
    ) -> TradeInResponse:
        method, path = self.function2interface(func_name)
        try:
            async with self.request_wrapper(
                method,
                self._make_url(path, name, query),
                self._make_headers(login_required, payload),
                payload,
            ) as resp:
                response_json = await resp.json()
                if convert_out:
                    if isinstance(response_json, list):
                        rv = []
                        for item in response_json:
                            rv.append(self.out2beehive(func_name, item))
                    else:
                        rv = self.out2beehive(func_name, response_json)
                else:
                    rv = response_json
                return TradeInResponse(data=rv, flag=True)
        except (ClientResponseError, ClientOSError, ServerDisconnectedError) as e:
            return TradeInResponse(msg=f"连接模拟交易系统失败, {e}.", flag=False)

    async def register_trade_system(self, **kwargs) -> TradeInResponse:
        """在交易系统注册账号.

        Parameters
        ----------
        **kwargs
            {"user_id": 用户id, "mobile": 手机号}

        Returns
        -------
            data={"fund_id": ""}
        """
        func_name = inspect.currentframe().f_code.co_name
        payload = {"capital": None, "desc": kwargs["user_id"]}
        return await self.request_interface(
            func_name=func_name, payload=payload, login_required=False
        )

    async def create_fund_account(self, **kwargs) -> TradeInResponse:
        """创建资金账户.

        Parameters
        ----------
        kwargs
            trade_user_id: 组合id
            total_input: 账户金额

        Returns
        -------
            data={"fund_id": ""}
        """
        func_name = inspect.currentframe().f_code.co_name
        out_payload = self.beehive2out(**kwargs)
        payload = {
            "capital": out_payload.get("capital"),
            "desc": out_payload.get("account_info"),
        }
        return await self.request_interface(
            func_name=func_name, payload=payload, login_required=False
        )

    async def bind_fund_account(self, **kwargs) -> TradeInResponse:
        """绑定资金账户.

        Parameters
        ----------
        kwargs
            trade_user_id: 交易用户id
            total_input: 账户金额

        Returns
        -------
            data={"fund_id": ""}
        """
        tir = await self.create_fund_account(**kwargs)
        return TradeInResponse(data={"fund_id": tir.data["fund_id"]}, flag=tir.flag)

    async def get_fund_account(self, **kwargs) -> TradeInResponse:
        """登陆并返回账户资产信息.

        Parameters
        ----------
        kwargs
            fund_id: 资金账户id

        Returns
        -------
            data=output_tuple.ACCOUNT
        """
        func_name = inspect.currentframe().f_code.co_name
        name = self.beehive2out(**kwargs)["account_id"]
        return await self.request_interface(
            func_name=func_name, name=name, login_required=False
        )

    async def get_fund_stock(self, **kwargs) -> TradeInResponse:
        """账户持仓查询.

        Parameters
        ----------
        kwargs
            fund_id: 资金账户id

        Returns
        -------
            data=output_tuple.POSITION
        """
        func_name = inspect.currentframe().f_code.co_name
        payload = self.beehive2out(**kwargs)
        tir = await self.request_interface(
            func_name=func_name, payload=payload, convert_out=False
        )
        if not tir.flag:
            return TradeInResponse(data=tir.data, flag=False)
        if kwargs.get("convert_out") is False:
            return TradeInResponse(data=tir.data, flag=True)

    async def get_fund_asset(self, **kwargs) -> TradeInResponse:
        """账户资产查询.

        Parameters
        ----------
        kwargs
            fund_id: 资金账户id

        Returns
        -------
            data=output_tuple.ASSET
        """
        func_name = inspect.currentframe().f_code.co_name
        name = self.beehive2out(**kwargs)["account_id"]
        convert_out = kwargs.get("convert_out", True)
        tir = await self.request_interface(
            func_name=func_name,
            name=name,
            login_required=False,
            convert_out=convert_out,
        )
        if not tir.flag:
            return TradeInResponse(data=tir.data, flag=False)
        if convert_out is False:
            return TradeInResponse(data=tir.data, flag=True)

    async def order_input(self, **kwargs) -> TradeInResponse:
        """交易.

        Parameters
        ----------
        kwargs:
            fund_id: 资金账户id
            symbol: "600001"
            exchange: "SH"
            order_price: 15.10
            order_direction: buy/sell
            order_quantity: 400
            order_date: str(datetime.today().date())
            order_time: str(datetime.today().time())

        Returns
        -------
            data: output_tuple.ORDER
        """
        func_name = inspect.currentframe().f_code.co_name
        out_order = self.beehive2out(**kwargs)
        return await self.request_interface(func_name=func_name, payload=out_order)

    async def order_cancel(self, **kwargs) -> TradeInResponse:
        """撤单.

        Parameters
        ----------
        kwargs
            fund_id: 资金账户ID
            order_id: 委托订单ID

        Returns
        -------
            data: 取消委托订单请求的执行状态文本
        """
        func_name = inspect.currentframe().f_code.co_name
        payload = self.beehive2out(**kwargs)
        name = payload["order_id"]
        return await self.request_interface(
            func_name=func_name, payload=payload, name=name, convert_out=False
        )

    async def get_today_orders(self, **kwargs) -> TradeInResponse:
        """
        操作记录查询（当日）
        """
        current_date = str(datetime.today().date())
        return await self.get_orders(
            start_date=current_date, stop_date=current_date, fund_id=kwargs["fund_id"]
        )

    async def get_orders(self, **kwargs) -> TradeInResponse:
        """
        操作记录查询（全部）
        """
        func_name = inspect.currentframe().f_code.co_name
        kwargs = self.beehive2out(**kwargs)
        query = {k: v for k, v in kwargs.items() if v is not None}
        payload = {"account_id": query.pop("account_id")}
        return await self.request_interface(
            func_name=func_name, query=query, payload=payload, convert_out=False
        )

    async def get_order_record(
        self, op_flag: int, fund_id, start_date="", stop_date=""
    ):
        """操作记录查询.

        Returns
        -------
            data=[output_tuple.ORDER_RECORD]
        """
        if start_date:
            start_date = self.beehive_date_to_pt_date(start_date)
        if stop_date:
            stop_date = self.beehive_date_to_pt_date(stop_date)
        if op_flag == 1:
            order_status = None
        elif op_flag == 2:
            order_status = "全部成交"
        elif op_flag == 3:
            order_status = "未成交"
        else:
            return TradeInResponse(msg="op_flag参数不正确", flag=False)
        tir = await self.get_orders(
            start_date=start_date,
            stop_date=stop_date,
            order_status=order_status,
            fund_id=fund_id,
        )
        return_data = []
        if tir.flag:
            for item in tir.data:
                try:
                    temp_data = self.out2beehive("get_orders", item)
                    temp_data["order_status_ex"] = item["status"]
                    temp_data["order_status"] = ORDER_STATUS[item["status"]]
                    temp_data["order_direction_ex"] = temp_data["order_direction"]
                    temp_data["exchange"] = EXCHANGE[temp_data["exchange"]]
                    security = await get_security_info(
                        temp_data["symbol"], temp_data["exchange"]
                    )
                    temp_data["symbol_name"] = security.symbol_name
                    temp_data["filled_amt"] = (
                        temp_data["trade_price"] * temp_data["trade_volume"]
                    )
                    temp_data["order_date"] = (
                        datetime.strptime(item["order_date"][:10], "%Y-%m-%d")
                        .date()
                        .strftime("%Y%m%d")
                    )
                    temp_data["order_time"] = item["order_date"][11:19]
                    return_data.append(temp_data)
                except Exception as e:
                    logging.info(f"委托单查询失败：{e}")
        return TradeInResponse(data=return_data or tir.data, flag=tir.flag)

    async def get_statement(self, **kwargs) -> TradeInResponse:
        """查询交割单."""
        if kwargs.get("start_date"):
            kwargs["start_date"] = self.beehive_date_to_pt_date(kwargs["start_date"])
        if kwargs.get("stop_date"):
            kwargs["stop_date"] = self.beehive_date_to_pt_date(kwargs["stop_date"])
        func_name = inspect.currentframe().f_code.co_name
        kwargs = self.beehive2out(**kwargs)
        query = {k: v for k, v in kwargs.items() if v is not None}
        payload = {"account_id": query.pop("account_id")}
        if kwargs.get("convert_out") is not None:
            query.pop("convert_out")
        tir = await self.request_interface(
            func_name=func_name, query=query, payload=payload, convert_out=False
        )
        if tir.flag and tir.data and kwargs.get("convert_out") is False:
            return TradeInResponse(flag=True, data=tir.data)
        return_data = []
        if tir.flag:
            for statement in tir.data:
                statement_data = self.out2beehive("get_statement", statement)
                statement_data["exchange"] = EXCHANGE[statement_data["exchange"]]
                # 查询的为交割单，故订单状态为 `全部成交` 即 4
                statement_data["order_status"] = "4"
                statement_data["total_fee"] = statement["costs"]["total"]
                statement_data["trade_date"] = datetime.strptime(
                    statement["deal_time"][:10], "%Y-%m-%d"
                )
                return_data.append(statement_data)
        return TradeInResponse(data=return_data or tir.data, flag=tir.flag)

    async def manual_clear(self, **kwargs):
        """
        手动清算
        Parameters
        ----------
        kwargs
            {
                "fund_id":
                "check_date":
                "price_dict": ujson.dumps({"600837.SH": 15.1})
            }
        Returns
        -------
            data="清算完成"
        """
        return TradeInResponse(data="清算完成", flag=True)

    async def close(self):
        await self._client.close()
