class TradeSystemAdaptor(object):
    def __init__(self):
        ...

    @staticmethod
    def out2beehive(func_name, data):
        """处理外部数据返回beehive的格式转换."""
        ...

    @staticmethod
    def beehive2out(**kwargs):
        """将外部的字段名改为beehive使用的规范字段名."""
        ...

    @staticmethod
    def function2endpoint(func_name):
        """返回该方法应该调用的接口的endpoint."""
        ...

    def register_trade_system(self, **kwargs):
        """在交易系统注册账号."""
        ...

    def create_fund_account(self, **kwargs):
        """创建资金账户."""
        ...

    def get_fund_account(self, **kwargs):
        """账户信息查询."""
        ...

    def get_fund_stock(self, **kwargs):
        """账户持仓查询."""
        ...

    def get_fund_asset(self, **kwargs):
        """账户资产查询."""
        ...

    def order_input(self, **kwargs):
        """交易."""
        ...

    def get_order_record(self, **kwargs):
        """操作记录查询."""
        ...

    def order_cancel(self, **kwargs):
        """撤单."""
        ...

    def manual_clear(self, **kwargs):
        """手动撤单."""
        ...

    def bind_fund_account(self, **kwargs):
        """绑定资金账户."""
        ...

    def get_statement(self, **kwargs):
        """交割单查询"""
        ...

    def close(self):
        """关闭交易系统连接."""
        ...


class TradeInterface:
    def __init__(self, backend_adaptor: TradeSystemAdaptor):
        self.backend_adaptor = backend_adaptor

    def register_trade_system(
        self,
        user_id: str,
        mobile: str = None,
    ):
        """在交易系统中注册帐号.

        Parameters
        ----------
        user_id: 用户id
        mobile: 手机号

        Returns
        ----------
        trade_user_id
        """
        return self.backend_adaptor.register_trade_system(
            user_id=user_id, mobile=mobile
        )

    def create_fund_account(
        self,
        portfolio_id: int,
        total_input: float,
    ):
        """创建资金账户.

        Parameters
        ----------
        portfolio_id: 组合id
        total_input: 账户金额
        """
        return self.backend_adaptor.create_fund_account(
            portfolio_id=portfolio_id, total_input=total_input
        )

    async def get_fund_account(self, fund_id: str):
        """资金账户信息查询.

        Parameters
        ----------
        fund_id: 资金账户id
        """
        return await self.backend_adaptor.get_fund_account(fund_id=fund_id)

    async def get_fund_stock(self, fund_id: str, convert_out: bool = True):
        """账户持仓查询.

        Parameters
        ----------
        fund_id: 资金账户id
        convert_out: 是否转换格式
        """
        return await self.backend_adaptor.get_fund_stock(
            fund_id=fund_id, convert_out=convert_out
        )

    async def get_fund_asset(self, fund_id: str, convert_out: bool = True):
        """账户资产查询.

        Parameters
        ----------
        fund_id: 资金账户id
        convert_out: 是否转换格式
        """
        return await self.backend_adaptor.get_fund_asset(
            fund_id=fund_id, convert_out=convert_out
        )

    def order_input(
        self,
        fund_id: str,
        symbol: str,
        exchange: str,
        order_price: float,
        order_direction: str,
        order_quantity: int,
        order_date: str,
        order_time: str,
        trade_type: str = "T1",
    ):
        """交易."""
        return self.backend_adaptor.order_input(
            fund_id=fund_id,
            symbol=symbol,
            exchange=exchange,
            order_price=order_price,
            order_direction=order_direction,
            order_quantity=order_quantity,
            order_date=order_date,
            order_time=order_time,
            trade_type=trade_type,
        )

    async def get_order_record(
        self,
        fund_id: str,
        start_date: str = None,
        stop_date: str = None,
        op_flag: int = 1,
    ):
        """委托记录查询.

        Parameters
        ----------
        fund_id: 资金账户id
        start_date: '20180101'
        stop_date: '20180606'
        op_flag: 1:委托 2:成交 3:可撤
        """
        return await self.backend_adaptor.get_order_record(
            start_date=start_date,
            stop_date=stop_date,
            op_flag=op_flag,
            fund_id=fund_id,
        )

    async def get_statement(
        self,
        fund_id: str,
        start_date: str = None,
        stop_date: str = None,
        convert_out: bool = True,
    ):
        """交割单记录查询.

        Parameters
        ----------
        fund_id: 资金账户id
        start_date: '20180101'
        stop_date: '20180606'
        convert_out: 是否转换格式
        """
        return await self.backend_adaptor.get_statement(
            start_date=start_date,
            stop_date=stop_date,
            fund_id=fund_id,
            convert_out=convert_out,
        )

    def order_cancel(self, fund_id: str, order_id: str):
        """撤单.

        Parameters
        ----------
        fund_id: 资金账户id
        order_id: 委托订单ID
        """
        return self.backend_adaptor.order_cancel(fund_id=fund_id, order_id=order_id)

    def manual_clear(
        self,
        fund_id: str,
        check_date: str,
        price_dict: dict,
    ):
        """手动清算.

        Parameters
        ----------
        fund_id: 资金账户id
        check_date: 检查日期
        price_dict: ujson.dumps({"600837.SH": 15.1})
        """
        return self.backend_adaptor.manual_clear(
            fund_id=fund_id, check_date=check_date, price_dict=price_dict
        )

    def bind_fund_account(
        self,
        trade_user_id: int,
        total_input: float,
    ):
        """绑定资金账户.

        Parameters
        ----------
        trade_user_id: 用户ID
        total_input: 初始资金
        """
        return self.backend_adaptor.bind_fund_account(
            trade_user_id=trade_user_id, total_input=total_input
        )

    def close(self):
        return self.backend_adaptor.close()
