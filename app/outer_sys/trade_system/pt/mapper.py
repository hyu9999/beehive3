from app.outer_sys.trade_system.pt import output_tuple

"""函数名对照外部接口的映射"""
INTERFACE = {
    "register_trade_system": ("POST", "auth/register"),
    "create_fund_account": ("POST", "auth/register"),
    "get_fund_account": ("GET", "users/"),
    "get_fund_stock": ("GET", "position/"),
    "get_fund_asset": ("GET", "users/"),
    "order_input": ("POST", "orders/"),
    "order_cancel": ("DELETE", "orders/entrust_orders/"),
    "get_orders": ("GET", "orders/"),
    "get_statement": ("GET", "statement/"),
}


"""input"""
INPUT = {
    "user_id": "",  # 模拟交易系统用户id
    "trade_user_id": "account_info",  # 对应智道账户id
    "fund_id": "account_id",  # 模拟交易系统资金账户id
    "order_id": "order_id",
    "symbol": "symbol",
    "order_price": "price",
    "exchange": "exchange",
    "order_quantity": "volume",
    "mobile": "mobile",
    "token": "token",
    "order_direction": "order_type",
    "order_date": "order_date",
    "order_time": "order_time",
    "start_date": "start_date",
    "stop_date": "end_date",
    "price_dict": "price_dict",
    "check_date": "check_date",
    "total_input": "capital",
    "portfolio_id": "account_info",
    "trade_type": "trade_type",
    "order_status": "status",
    "convert_out": "convert_out",
}


"""output"""
OUTPUT = {
    "register_trade_system": output_tuple.REGISTER,
    "create_fund_account": output_tuple.ACCOUNT,
    "get_fund_account": output_tuple.ACCOUNT,
    "get_fund_asset": output_tuple.ASSET,
    "get_fund_stock": output_tuple.POSITION,
    "get_today_orders": output_tuple.ORDER_RECORD,
    "get_orders": output_tuple.ORDER_RECORD,
    "get_statement": output_tuple.STATEMENT,
    "order_input": output_tuple.ORDER,
}


ORDER_STATUS = {
    "提交中": "0",
    "未成交": "1",
    "已拒单": "2",
    "部分成交": "3",
    "全部成交": "4",
    "已撤销": "6",
}

EXCHANGE = {"SH": "1", "SZ": "0"}

ORDER_DIRECTION = {"buy": "0", "sell": "1"}
