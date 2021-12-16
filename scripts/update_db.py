import logging
import pymongo as pymongo

from app import settings


def update_robot(db: pymongo.MongoClient):
    """
    v1.0 update to v1.1:update robot_collection 风控包标识符->风控包列表
    """
    robots_cursor = db[settings.db.DB_NAME][settings.collections.ROBOT].find({"风控包标识符": {"$ne": None}})
    for row in robots_cursor:
        db[settings.db.DB_NAME][settings.collections.ROBOT].update_one({"标识符": row["标识符"]}, {"$set": {"风控包标识符": None, "风控包列表": [row["风控包标识符"]]}})
    result = db[settings.db.DB_NAME][settings.collections.ROBOT].find_one({"风控包标识符": {"$ne": None}})
    if not result:
        logging.info(f"更新robot成功。\n")
    else:
        logging.info(f"更新robot失败。\n")


def update_user_robot(db: pymongo.MongoClient):
    """
    v1.0 update to v1.1:update users_collection 风控包标识符->风控包列表
    """
    result = db[settings.db.DB_NAME][settings.collections.USER].find({"robot": {"$ne": None}})
    for row in result:
        if row["robot"]:
            robots = []
            for robot in row["robot"]:
                if robot.get("风控包标识符", None):
                    robot["风控包列表"] = [robot.pop("风控包标识符")]
                robots.append(robot)
            db[settings.db.DB_NAME][settings.collections.USER].update_one({"username": row["username"]}, {"$set": {"robot": robots}})


def update_tags(db: pymongo.MongoClient):
    """
    v1.0 update to v1.1:将robot/equipment中tag去重分类写入tags_collection_name
    """
    robots_cursor = db[settings.db.DB_NAME][settings.collections.ROBOT].find({})
    robts_tags = {tag for row in robots_cursor for tag in row["标签"]}
    robts_tag_list = []
    for tag in robts_tags:
        if tag not in robts_tag_list:
            robts_tag_list.append({"名称": tag, "类型": "机器人"})
    result = db[settings.db.DB_NAME][settings.collections.TAG].insert_many(robts_tag_list)
    if not result.inserted_ids:
        logging.info(f"更新robot_tag失败。\n")
        return
    logging.info(f"更新robot_tag成功。\n")

    equipments_cursor = db[settings.db.DB_NAME][settings.collections.EQUIPMENT].find({})
    equipments_tags = {tag for row in equipments_cursor for tag in row["标签"]}
    equipments_tag_list = []
    for tag in equipments_tags:
        if tag not in equipments_tag_list:
            equipments_tag_list.append({"名称": tag, "类型": "装备"})
    result = db[settings.db.DB_NAME][settings.collections.TAG].insert_many(equipments_tag_list)
    if not result.inserted_ids:
        logging.info(f"更新equipment_tag失败。\n")
        return
    logging.info(f"更新equipment_tag成功。\n")

    packages_cursor = db[settings.db.DB_NAME]["packages"].find({})
    packages_tags = {tag for row in packages_cursor for tag in row["标签"]}
    packages_tag_list = []
    for tag in packages_tags:
        if tag not in packages_tag_list:
            packages_tag_list.append({"名称": tag, "类型": "装备"})
    result = db[settings.db.DB_NAME][settings.collections.TAG].insert_many(packages_tag_list)
    if not result.inserted_ids:
        logging.info(f"更新packages_tag失败。\n")
        return
    logging.info(f"更新packages_tag成功。\n")


def update_user_nickname(db: pymongo.MongoClient):
    user_cursor = db[settings.db.DB_NAME][settings.collections.USER].find({})
    for row in user_cursor:
        if row["username"].isdigit():
            db[settings.db.DB_NAME][settings.collections.USER].update_many({"username": row["username"]}, {"$set": {"nickname": f"用户{row['username'][-4:]}"}})
        elif len(row["username"]) < 11:
            db[settings.db.DB_NAME][settings.collections.USER].update_many({"username": row["username"]}, {"$set": {"nickname": row["username"]}})


def migrate_package(db: pymongo.MongoClient):
    """
    v1.0 update to v1.1:将robot/equipment中tag去重分类写入tags_collection_name
    """
    packages_cursor = db[settings.db.DB_NAME]["packages"].find({})
    packages_list = [row for row in packages_cursor]
    result = db[settings.db.DB_NAME][settings.collections.EQUIPMENT].insert_many(packages_list)
    if not result.inserted_ids:
        logging.info(f"packages迁移失败。\n")
        return
    logging.info(f"packages迁移成功。\n")
    db[settings.db.DB_NAME]["packages"].drop()


def update_site_configs(db: pymongo.MongoClient):
    """
    v1.6.0
    """
    site_init_configs = [
        {"配置名称": "大类资产配置回测指标collection名", "值": "回测指标.大类资产配置", "配置说明": "大类资产配置回测指标collection名", "配置标签": ["大类资产配置", "回测指标"], "配置分类": "装备"},
        {"配置名称": "基金定投回测指标collection名", "值": "回测指标.基金定投", "配置说明": "基金定投回测指标collection名", "配置标签": ["基金定投", "回测指标"], "配置分类": "装备"},
        {"配置名称": "大类资产配置回测信号collection名", "值": "回测信号.大类资产配置", "配置说明": "大类资产配置回测信号collection名", "配置标签": ["大类资产配置", "回测信号", "回测"], "配置分类": "装备"},
        {"配置名称": "基金定投回测信号collection名", "值": "回测信号.基金定投", "配置说明": "基金定投回测信号collection名", "配置标签": ["基金定投", "回测信号", "回测"], "配置分类": "装备"},
        {"配置名称": "大类资产配置回测评级collection名", "值": "回测评级.大类资产配置", "配置说明": "大类资产配置回测评级collection名", "配置标签": ["大类资产配置", "回测评级"], "配置分类": "装备"},
        {"配置名称": "基金定投回测评级collection名", "值": "回测评级.基金定投", "配置说明": "基金定投回测评级collection名", "配置标签": ["基金定投", "回测评级"], "配置分类": "装备"},
        {"配置名称": "大类资产配置实盘信号collection名", "值": "实盘信号.大类资产配置", "配置说明": "大类资产配置实盘信号collection名", "配置标签": ["大类资产配置", "实盘信号", "实盘"], "配置分类": "装备"},
        {"配置名称": "基金定投实盘信号collection名", "值": "实盘信号.基金定投", "配置说明": "基金定投实盘信号collection名", "配置标签": ["基金定投", "实盘信号", "实盘"], "配置分类": "装备"},
        {"配置名称": "大类资产配置实盘指标collection名", "值": "实盘指标.大类资产配置", "配置说明": "大类资产配置实盘指标collection名", "配置标签": ["大类资产配置", "实盘指标"], "配置分类": "装备"},
        {"配置名称": "基金定投实盘指标collection名", "值": "实盘指标.基金定投", "配置说明": "基金定投实盘指标collection名", "配置标签": ["基金定投", "实盘指标"], "配置分类": "装备"},
    ]
    collection = db[settings.db.DB_NAME]["site_configs"]
    result = collection.insert_many(site_init_configs)
    if not result.inserted_ids:
        logging.info(f"site_configs更新大类资产配置和基金定投失败。\n")
        return
    logging.info(f"site_configs更新大类资产配置和基金定投成功。\n")


def update_permissions_and_roles(db: pymongo.MongoClient):
    result = db[settings.db.DB_NAME]["roles"].insert_one({"角色名称": "VIP用户"})
    if result.inserted_id:
        logging.info(f"新增vip用户角色成功！")
    else:
        logging.info(f"新增vip用户角色失败！")
    result = db[settings.db.DB_NAME]["permissions"].update_one(
        {"角色": "免费用户"},
        {"$set": {"权限": {"装备": ["查看", "修改", "订阅"], "机器人": ["查看", "修改", "订阅"], "稻草人数据": ["查看"], "包": ["查看", "修改", "订阅"], "投资原则": ["查看"], "用户": ["查看"]}}},
    )
    if result.modified_count:
        logging.info(f"免费用户权限更新成功！")
    else:
        logging.info(f"免费用户权限更新失败！")
    result = db[settings.db.DB_NAME]["permissions"].insert_one(
        {
            "角色": "VIP用户",
            "权限": {
                "装备": ["查看", "创建", "修改", "订阅"],
                "机器人": ["查看", "创建", "修改", "订阅"],
                "稻草人数据": ["查看"],
                "包": ["查看", "创建", "修改", "订阅"],
                "投资原则": ["查看"],
                "用户": ["查看"],
            },
        }
    )
    if result.inserted_id:
        logging.info(f"VIP用户权限新增成功！")
    else:
        logging.info(f"VIP用户权限新增失败！")


db = pymongo.MongoClient(settings.db.MONGODB_URL, maxPoolSize=settings.db.MAX_CONNECTIONS, minPoolSize=settings.db.MAX_CONNECTIONS)
versions = input("请输入更新版本：\n")
if versions == "1.1":
    logging.basicConfig(level=logging.INFO)
    update_robot(db)
    update_user_robot(db)
    update_tags(db)
    migrate_package(db)
elif versions == "1.3.5":
    update_user_nickname(db)
elif versions == "1.6.0":
    update_site_configs(db)
elif versions == "1.6.5":
    update_permissions_and_roles(db)
else:
    pass
