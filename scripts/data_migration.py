"""
数据迁移脚本：将beehive2的数据迁移到新的beehive3数据库中
"""
from datetime import datetime

from pymongo import MongoClient

DB_NAME = "beehive_2_5_dev"
HOST = "123.103.74.231"
PORT = 27717
USERNAME = "root"
PASSWORD = "jinniuchuangzhi123"

DB_NAME3 = "beehive3_master"
HOST3 = "123.103.74.231"
PORT3 = 27717
USERNAME3 = "root"
PASSWORD3 = "jinniuchuangzhi123"

db_param = {
    "host": HOST,
    "port": PORT,
    "username": USERNAME,
    "password": PASSWORD,
    "connect": False,
}
db_param3 = {
    "host": HOST3,
    "port": PORT3,
    "username": USERNAME3,
    "password": PASSWORD3,
    "connect": False,
}


class MongoUtils:
    def __init__(self, param, db_name):
        self.client = MongoClient(**param)
        self.db = self.client[db_name]

    def query(self, table_name, condition=None, include=None):
        collection = self.db[table_name]
        condition = condition or {}
        include = include
        cursor = collection.find(condition, include)
        ret_data = []
        for doc in cursor:
            ret_data.append(doc)
        return ret_data

    def query_one(self, table_name, condition=None):
        collection = self.db[table_name]
        condition = condition or {}
        ret_data = collection.find_one(condition)
        return ret_data

    def insert(self, table_name, content=None):
        collection = self.db[table_name]
        content = content or {}
        cursor = collection.insert_one(content)
        return cursor.inserted_id

    def update_one(self, table_name, filters, content=None):
        collection = self.db[table_name]
        content = content or {}
        cursor = collection.update_one(filters, {"$set": content}, upsert=True)
        return cursor.upserted_id

    def update_many(self, table_name, filters, content=None):
        collection = self.db[table_name]
        content = content or {}
        cursor = collection.update_many(filters, {"$set": content}, upsert=True)
        return cursor.upserted_id

    def close(self):
        self.client.close()


# 不用动
字典表 = {
    "stock_statistics_conf": "stock_stats_conf",
    "trade_statistics_conf": "trade_stats_conf",
    "portfolio_tags": "tag",
    "portfolio_target": "portfolio_target_conf",
}
数据表 = {
    "user_user": "user",
    "portfolio": "portfolio",
    "activity": "activity",
    "activity_yield_log": "activity_yield_log",
    "favorite_list": "favorite_stock",
    "order": "order",
    "stock_log": "stock_log",
    "trend_chart": "trend_chart",
}


def format_stock_stats_conf(db2, data):
    print(f"data=={data}")
    ret_data = {
        "name": data["name"],
        "code": data["en_name"],
    }
    filters = {"name": data["name"]}
    return filters, ret_data


def format_trade_stats_conf(db2, data):
    ret_data = {
        "name": data["name"],
        "code": data["en_name"],
    }
    filters = {"name": data["name"]}
    return filters, ret_data


def format_tag(db2, data):
    ret_data = {
        "类型": "组合",
        "名称": data["name"],
    }
    filters = {"类型": "组合", "名称": data["name"]}
    return filters, ret_data


def format_portfolio_target_conf(db2, data):
    ret_data = {
        "name": data["name"],
        "code": data["code"],
    }
    filters = {"name": data["name"]}
    return filters, ret_data


def format_user(db2, data):
    status_dict = {
        "正常": "normal",
        "禁用": "disable",
        "注销": "log_off",
        "首次": "first",
    }
    if data.get("account_info", ""):
        account = data.get("account_info", "")
    else:
        account = {"status": 0, "is_tried": False, "expired_at": datetime.utcnow()}
    ret_data = {
        "_id": data["_id"],
        "username": data["username"],
        "nickname": data["nickname"],
        "email": data.get("email", None),
        "introduction": data.get("introduction", ""),
        "avatar": data.get("avatar", None),
        "mobile": data.get("mobile", None) or None,
        "account": account,
        "open_id": data.get("open_id", None),
        "union_id": data.get("weixinid", None),
        "send_flag": data.get("send_flag", True),
        "disc_id": data.get("disc_id", None),
        "send_type": "not_send",
        "roles": ["免费用户"],
        "status": status_dict[data["status"]] if data["status"] else "normal",
    }
    filters = {"username": data["username"]}
    return filters, ret_data


def format_portfolio(db2, data):
    try:
        user = db2.query_one("user_user", {"_id": data["user"]})
    except Exception as e:
        print(data["user"])
        raise
    else:
        try:
            username = user["username"]
        except Exception as e:
            print(data["user"])
            print(user)
            raise ValueError("创建组合的账户异常，查询不到该用户的信息")
    robot_config = data["robot_config"]
    robot_config["open_risks"] = data["robot"].get("open_risks", [])
    old_tags = data.get("tags", [])
    tags = []
    for i in old_tags:
        name = db2.query_one("portfolio_tags", {"_id": i})["name"]
        tags.append(name)

    ret_data = {
        "_id": data["_id"],
        "name": data["name"],
        "status": "running" if data["status"] == "1" else "closed",
        "username": username,
        "fund_account": data["fund_account"],
        "initial_funding": data["total_input"],
        "invest_type": "stock",
        "tags": tags,
        "introduction": data.get("introduction", ""),
        "config": data["config"],
        "robot_config": robot_config,
        "risks": data.get("risks", []),
        "is_open": data["is_open"],
        "robot": data["robot"]["_id"],
        "subscribe_num": data.get("subscribe_num", 0),
        "article_id": data.get("article_id", None),
        "close_date": data.get("end_date"),
        "create_date": data.get("create_date"),
    }
    filters = {"_id": data["_id"]}
    return filters, ret_data


def format_activity(db2, data):
    status_dict = {
        0: "pre_online",
        1: "online",
        2: "offline",
        3: "deleted",
    }

    ret_data = {
        "_id": data["_id"],
        "name": data["name"],
        "banner": data.get("banner", None),
        "detail_img": data.get("big_banner", None),
        "start_time": data["start_time"],
        "end_time": data["end_time"],
        "introduction": data["introduction"],
        "status": status_dict[data["status"]],
    }
    filters = {"_id": data["_id"]}
    return filters, ret_data


def format_activity_yield_log(db2, data):
    ret_data = {
        "_id": data["_id"],
        "portfolio_name": data.get("name"),
        "profit_rate": data.get("profit_rate", None),
        "rank": data.get("rank", None),
        "over_percent": data.get("over_percent"),
        "activity": data.get("activity_id"),
        "portfolio": data.get("portfolio_id"),
    }
    filters = {"_id": data["_id"]}
    return filters, ret_data


def format_order(db2, data):
    username = db2.query_one("user_user", {"_id": data["user"]})["username"]
    买卖方向 = {1: "buy", 0: "sell"}
    ret_data = {
        "_id": data["_id"],
        "symbol": data.get("symbol"),
        "exchange": data.get("exchange", None),
        "symbol_name": data.get("symbol_name", None),
        "username": username,
        "task": data.get("task_id", None),
        "portfolio": data.get("portfolio"),
        "create_datetime": data.get("create_datetime"),
        "end_datetime": data.get("end_datetime"),
        "order_id": data.get("order_id"),
        "fund_id": data.get("fund_id", None),
        "status": data.get("status"),
        "finished_quantity": data.get("finished_quantity"),
        "average_price": data.get("average_price"),
        "operator": 买卖方向[data.get("operator")],
        "price": data.get("price"),
        "quantity": data.get("quantity"),
    }
    filters = {"_id": data["_id"]}
    return filters, ret_data


def format_stock_log(db2, data):
    买卖方向 = {"0": "buy", "1": "sell", "unknown": "unknown"}
    ret_data = {
        "_id": data["_id"],
        "portfolio": data.get("portfolio"),
        "symbol": data.get("symbol"),
        "exchange": "1" if data.get("exchange", None) in [1, "1", "上海"] else "0",
        "symbol_name": data.get("symbol_name", None),
        "sno": data.get("symbol_name", None),
        "order_quantity": data.get("order_quantity", None),
        "order_id": data.get("order_id"),
        "order_time": data.get("order_time"),
        "order_direction": 买卖方向[data.get("order_direction", "unknown")],
        "order_price": data.get("order_price", None),
        "order_volume": data.get("order_volume"),
        "order_status": data.get("order_status", "9") if isinstance(data.get("order_status", "9"), str) else str(data.get("order_status", "9")),
        "trade_date": data.get("trade_date"),
        "trade_time": data.get("trade_time"),
        "trade_price": data.get("trade_price"),
        "trade_volume": data.get("trade_volume"),
        "stkeffect": data.get("stkeffect"),
        "stock_quantity": data.get("stock_quantity"),
        "fundeffect": data.get("fundeffect"),
        "fundbal": data.get("fundbal"),
        "degestid": data.get("degestid"),
        "stamping": data.get("stamping"),
        "transfer_fee": data.get("transfer_fee"),
        "commission": data.get("commission"),
        "total_fee": data.get("total_fee"),
        "filled_amt": data.get("filled_amt"),
        "settlement_fee": data.get("settlement_fee"),
        "order_date": data.get("order_date"),
        "ttype": data.get("ttype"),
    }
    filters = {"_id": data["_id"]}
    return filters, ret_data


def format_trend_chart(db2, data):
    ret_data = {
        "_id": data["_id"],
        "category": data["category"],
        "tdate": data["tdate"],
        "max_drawdown": data["max_drawdown"],
        "profit_rate": data["profit_rate"],
    }
    filters = {"_id": data["_id"]}
    return filters, ret_data


def format_favorite_stock(db2, data):
    username = db2.query_one("user_user", {"_id": data["user_id"]})["username"]
    unowned_stocks = data.get("unowned_stocks", [])
    for i in unowned_stocks:
        i["stop_profit"] = 9999
        i["stop_loss"] = 0
    ret_data = {
        "username": username,
        "category": "portfolio",
        "sid": None,
        "stocks": unowned_stocks,
    }
    filters = {"username": username, "category": "portfolio"}
    return filters, ret_data


def sync_data(db2, db3, db2_col, db3_col):
    queryset = db2.query(db2_col)
    for p in queryset:
        # 重复的用户不更新
        if db3_col == "user":
            if db3.query_one("user", {"username": p["username"]}):
                # print(f"已存在的用户============{p['username']}")
                continue
        try:
            filters, content = format_data(db2, db3_col, p)
        except Exception as e:
            print(f"=={e}")
            continue
        db3.update_one(db3_col, filters, content)


def format_data(db2, db3_col, data):
    return eval(f"format_{db3_col}(db2, data)")


def update_user_data(db2, db3):
    target_config = {
        "trade_stats": [
            {"code": "trade_cost", "name": "交易成本"},
            {"code": "winning_rate", "name": "交易胜率"},
            {"code": "trade_frequency", "name": "总交易次数"},
            {"code": "profit_loss_ratio", "name": "盈亏比"},
        ],
        "stock_stats": [{"code": "income", "name": "收益"}, {"code": "sell_num", "name": "交易次数"},],
        "portfolio_target": [{"code": "10001", "name": "当日盈亏"}, {"code": "10002", "name": "总资产"},],
    }
    equipment = {
        "subscribe_info": {"fans_num": 0, "focus_num": 0, "focus_list": []},
        "create_info": {"create_num": 0, "running_list": [], "closed_list": []},
        "msg_num": 0,
    }
    robot = {
        "subscribe_info": {"fans_num": 0, "focus_num": 0, "focus_list": []},
        "create_info": {"create_num": 0, "running_list": [], "closed_list": []},
        "msg_num": 0,
    }
    portfolio = {
        "subscribe_info": {"fans_num": 0, "focus_num": 0, "focus_list": []},
        "create_info": {"create_num": 0, "running_list": [], "closed_list": []},
        "msg_num": 0,
    }
    db3.update_many(
        "user", {}, content={"target_config": target_config, "equipment": equipment, "robot": robot, "portfolio": portfolio,},
    )


def update_user_create_or_subscribe(db2, db3):
    user_queryset = db3.query("user")
    for u in user_queryset:
        equip = db3.query("equipment", {"作者": u["username"], "状态": {"$in": ["已上线", "已下线"]}}, {"标识符": 1, "状态": 1},)
        robot = db3.query("robot", {"作者": u["username"], "状态": {"$in": ["已上线", "已下线"]}}, {"标识符": 1, "状态": 1},)
        portfolio = db3.query("portfolio", {"username": u["username"]}, {"_id": 1, "status": 1})
        db3.update_one(
            "user",
            {"_id": u["_id"]},
            {
                "equipment.create_info": {
                    "create_num": len(equip),
                    "running_list": [x["标识符"] for x in equip if x["状态"] == "已上线"],
                    "closed_list": [x["标识符"] for x in equip if x["状态"] == "已下线"],
                },
                "robot.create_info": {
                    "create_num": len(robot),
                    "running_list": [x["标识符"] for x in robot if x["状态"] == "已上线"],
                    "closed_list": [x["标识符"] for x in robot if x["状态"] == "已下线"],
                },
                "portfolio.create_info": {
                    "create_num": len(portfolio),
                    "running_list": [x["_id"] for x in portfolio if x["status"] == "running"],
                    "closed_list": [x["_id"] for x in portfolio if x["status"] == "closed"],
                },
            },
        )


def main_func():
    db2 = MongoUtils(db_param, DB_NAME)
    db3 = MongoUtils(db_param3, DB_NAME3)
    for k, v in 字典表.items():
        print(f"{k}===开始同步数据")
        sync_data(db2, db3, k, v)
        print(f"{k}===同步数据成功\n\n")

    for k, v in 数据表.items():
        print(f"{k}===开始同步数据")
        sync_data(db2, db3, k, v)
        print(f"{k}===同步数据成功\n\n")
    update_user_data(db2, db3)

    update_user_create_or_subscribe(db2, db3)


if __name__ == "__main__":
    """
    """
    main_func()
