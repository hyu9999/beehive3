# 账户注册
REGISTER = (
    ("fund_id", "_id", ""),
)


# 账户转化
ACCOUNT = (
    ("fund_name", "desc", ""),  # 资金账户名称
    ("fund_id", "_id", ""),  # 资金账号
    ("total_capital", "capital", ""),  # 总资产
)

# 资产转化
ASSET = (
    ("fund_id", "_id", ""),  # 资金账号
    ("capital", "capital", 0),  # 初始资金
    ("total_capital", "assets", 0),  # 总资产
    ("fund_balance", "-", 0),  # 资金余额
    ("fund_available", "available_cash", 0),  # 可用余额
    ("fund_depositable", "-", "0"),  # 可取余额,为0
    ("market_value", "securities", 0),  # 市值
    ("total_profit", "-", 0),  # 总收益
    ("total_profit_rate", "-", 0),  # 总收益率
    ("stock_hold_list", "-", ""),  # 当前持仓信息??
)

# 持仓转化
POSITION = (
    ("fund_id", "_id", 0),  # 资金账号
    ("security_account", "_id", 0),  # 证券账号
    ("exchange", "exchange", ""),  # 交易所
    ("symbol", "symbol", ""),  # 证券代码
    ("stock_quantity", "volume", 0),  # 持仓数量
    ("stock_available_quantity", "available_volume", 0),  # 持仓可用数量
    ("fund_in_transit", "-", 0),  # 在途资金??
    ("fund_freezing", "-", 0),  # 冻结资金??
    ("share_cost_price", "cost", 0),  # 证券持仓成本??
    ("buy_price", "cost", 0),  # 买入价格
    ("realtime_price", "current_price", 0),  # 当前价格
    ("market_value", "-", 0),  # 市值??
    ("float_profit", "profit", 0),  # 浮动盈亏??
    ("profit_rate_stock", "-", 0),  # 个股盈亏比率??
    ("symbol_name", "-", ""),  # 证券名称??
    ("buy_date", "first_buy_date", ""),  # 买入日期
    ("avg_price", "cost", ""),
    ("tprice", "cost", ""),
)


# 订单转化
ORDER_RECORD = (
    ("trade_user_id", "user", ""),  # 交易系统用户id
    ("fund_id", "user", ""),  # 资金账户
    ("security_account", "user", ""),  # 证券账号
    ("symbol_name", "-", ""),  # 证券名称
    ("symbol", "symbol", ""),  # 证券代码
    ("exchange", "exchange", ""),  # 交易所
    ("order_id", "entrust_id", ""),  # 委托单号
    ("order_price", "price", ""),  # 委托价格
    ("order_direction", "order_type", ""),  # 买卖方向
    ("order_direction_ex", "order_type", ""),  # 买卖方向翻译
    ("order_status", "status", ""),  # 委托状态
    ("order_status_ex", "status_ex", ""),  # 委托状态翻译
    ("order_quantity", "volume", ""),  # 委托数量
    ("order_date", "order_date", ""),  # 委托日期
    ("order_time", "created_at", ""),  # 委托时间
    ("filled_amt", "-", ""),  # 成交金额
    ("trade_price", "sold_price", 0),  # 成交价格
    ("trade_volume", "traded_volume", 0),  # 成交数量
    ("trade_date", "order_date", ""),  # 成交日期
    ("trade_time", "deal_time", ""),  # 成交时间
    ("total_fee", "-", 0),  # 总交易费用
    ("transfer_fee", "-", 0),  # 过户费
    ("commission", "-", 0),  # 佣金
    ("stamping", "-", 0),  # 印花税
    ("settlement_fee", "-", 0),  # 结算费
    ("position_change", "position_change", 0),  # 仓位变化
)

# 合同号转化
ORDER = (("order_id", "entrust_id", ""),)

# 交割单
STATEMENT = (
    ("trade_user_id", "user", ""),  # 交易系统用户id
    ("fund_id", "user", ""),  # 资金账户
    ("security_account", "user", ""),  # 证券账号
    ("symbol", "symbol", ""),  # 证券代码
    ("exchange", "exchange", ""),  # 交易所
    ("order_id", "entrust_id", ""),  # 委托单号
    ("order_direction", "trade_category", ""),  # 买卖方向
    ("order_quantity", "volume", ""),  # 成交数量
    ("filled_amt", "amount", ""),  # 成交金额
    ("trade_price", "sold_price", 0),  # 成交价格
    ("total_fee", "-", 0),  # 总交易费用
    ("commission", "-", 0),  # 佣金
    ("stamping", "-", 0),  # 印花税
    ("deal_time", "deal_time", ""),
)
