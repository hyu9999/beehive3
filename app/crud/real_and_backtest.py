def get_实盘回测_filter(collection_name, data):
    ret_data = {"标识符": data.标识符}
    if collection_name in [
        "选股回测信号collection名",
        "选股实盘信号collection名",
        "机器人回测指标collection名",
        "机器人实盘指标collection名",
        "大类资产配置回测指标collection名",
        "基金定投回测指标collection名",
        "大类资产配置实盘指标collection名",
        "基金定投实盘指标collection名",
    ]:
        ret_data = {"标识符": data.标识符, "交易日期": data.交易日期}
    elif collection_name in ["选股回测指标collection名"]:
        ret_data = {"标识符": data.标识符, "开始时间": data.开始时间, "结束时间": data.结束时间}
    elif collection_name in ["择时回测信号collection名", "择时实盘信号collection名"]:
        ret_data = {"标识符": data.标识符, "交易日期": data.交易日期, "标的指数": data.标的指数}
    elif collection_name in ["择时回测指标collection名", "择时回测评级collection名"]:
        ret_data = {"标识符": data.标识符, "标的指数": data.标的指数, "回测年份": data.回测年份}
    elif collection_name in ["选股回测评级collection名", "机器人回测评级collection名", "大类资产配置回测评级collection名", "基金定投回测评级collection名"]:
        ret_data = {"标识符": data.标识符, "数据集": data.数据集}
    elif collection_name in [
        "机器人回测信号collection名",
        "机器人实盘信号collection名",
        "大类资产配置回测信号collection名",
        "基金定投回测信号collection名",
        "大类资产配置实盘信号collection名",
        "基金定投实盘信号collection名",
    ]:
        ret_data = {"标识符": data.标识符, "交易日期": data.交易日期, "证券代码": data.证券代码, "交易市场": data.交易市场}
    return ret_data
