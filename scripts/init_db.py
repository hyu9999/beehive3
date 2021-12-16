import asyncio
import getpass
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, TEXT
from pymongo.errors import BulkWriteError, CollectionInvalid, DuplicateKeyError

from app import settings
from app.crud.user import create_user
from app.schema.user import UserInCreate


async def create_collection(db: AsyncIOMotorDatabase, name: str):
    try:
        await db.create_collection(name)
    except CollectionInvalid as e:
        logging.debug(e)
    else:
        logging.debug(f"创建{settings.collections.USER}成功\n")


site_init_configs = [
    {
        "配置名称": "装备信息collection名",
        "值": "equipment",
        "配置说明": "装备信息所在的collection名",
        "配置标签": ["装备"],
        "配置分类": "装备数据库",
    },
    {
        "配置名称": "装备话术collection名",
        "值": "verbal",
        "配置说明": "装备话术所在的collection名",
        "配置标签": ["装备", "话术"],
        "配置分类": "装备数据库",
    },
    {
        "配置名称": "机器人信息collection名",
        "值": "robot",
        "配置说明": "机器人信息数据所在的collection名",
        "配置标签": ["机器人"],
        "配置分类": "strawmandata数据库",
    },
    {
        "配置名称": "佣金率",
        "值": "0.01",
        "配置说明": "统一的佣金率设置",
        "配置标签": ["机器人"],
        "配置分类": "strawmandata数据库",
    },
    {
        "配置名称": "新注册用户的初始角色",
        "值": "免费用户",
        "配置说明": "新注册用户系统自动给与的初始角色",
        "配置标签": ["用户"],
        "配置分类": "用户",
    },
    {
        "配置名称": "组合信息collection名",
        "值": "portfolio",
        "配置说明": "组合信息所在的collection名",
        "配置标签": ["组合"],
        "配置分类": "组合数据库",
    },
    {
        "配置名称": "机器人回测指标collection名",
        "值": "回测指标.机器人",
        "配置说明": "机器人回测指标collection名",
        "配置标签": ["机器人", "回测指标"],
        "配置分类": "机器人",
    },
    {
        "配置名称": "机器人回测信号collection名",
        "值": "回测信号.机器人",
        "配置说明": "机器人回测信号collection名",
        "配置标签": ["机器人", "回测信号", "回测"],
        "配置分类": "机器人",
    },
    {
        "配置名称": "机器人回测评级collection名",
        "值": "回测评级.机器人",
        "配置说明": "机器人回测评级collection名",
        "配置标签": ["机器人", "回测评级"],
        "配置分类": "机器人",
    },
    {
        "配置名称": "选股回测指标collection名",
        "值": "回测指标.选股装备",
        "配置说明": "选股回测指标collection名",
        "配置标签": ["选股装备", "回测指标"],
        "配置分类": "装备",
    },
    {
        "配置名称": "择时回测指标collection名",
        "值": "回测指标.择时装备",
        "配置说明": "择时回测指标collection名",
        "配置标签": ["择时装备", "回测指标"],
        "配置分类": "装备",
    },
    {
        "配置名称": "大类资产配置回测指标collection名",
        "值": "回测指标.大类资产配置",
        "配置说明": "大类资产配置回测指标collection名",
        "配置标签": ["大类资产配置", "回测指标"],
        "配置分类": "装备",
    },
    {
        "配置名称": "基金定投回测指标collection名",
        "值": "回测指标.基金定投",
        "配置说明": "基金定投回测指标collection名",
        "配置标签": ["基金定投", "回测指标"],
        "配置分类": "装备",
    },
    {
        "配置名称": "择时回测信号collection名",
        "值": "回测信号.择时装备",
        "配置说明": "择时回测信号collection名",
        "配置标签": ["择时装备", "回测信号", "回测"],
        "配置分类": "装备",
    },
    {
        "配置名称": "选股回测信号collection名",
        "值": "回测信号.选股装备",
        "配置说明": "选股回测信号collection名",
        "配置标签": ["选股装备", "回测信号", "回测"],
        "配置分类": "装备",
    },
    {
        "配置名称": "大类资产配置回测信号collection名",
        "值": "回测信号.大类资产配置",
        "配置说明": "大类资产配置回测信号collection名",
        "配置标签": ["大类资产配置", "回测信号", "回测"],
        "配置分类": "装备",
    },
    {
        "配置名称": "基金定投回测信号collection名",
        "值": "回测信号.基金定投",
        "配置说明": "基金定投回测信号collection名",
        "配置标签": ["基金定投", "回测信号", "回测"],
        "配置分类": "装备",
    },
    {
        "配置名称": "选股回测评级collection名",
        "值": "回测评级.选股装备",
        "配置说明": "选股装备回测评级collection名",
        "配置标签": ["选股装备", "回测评级"],
        "配置分类": "装备",
    },
    {
        "配置名称": "择时回测评级collection名",
        "值": "回测评级.择时装备",
        "配置说明": "择时装备回测评级collection名",
        "配置标签": ["择时装备", "回测评级"],
        "配置分类": "装备",
    },
    {
        "配置名称": "大类资产配置回测评级collection名",
        "值": "回测评级.大类资产配置",
        "配置说明": "大类资产配置回测评级collection名",
        "配置标签": ["大类资产配置", "回测评级"],
        "配置分类": "装备",
    },
    {
        "配置名称": "基金定投回测评级collection名",
        "值": "回测评级.基金定投",
        "配置说明": "基金定投回测评级collection名",
        "配置标签": ["基金定投", "回测评级"],
        "配置分类": "装备",
    },
    {
        "配置名称": "机器人实盘信号collection名",
        "值": "实盘信号.机器人",
        "配置说明": "机器人实盘信号collection名",
        "配置标签": ["机器人", "实盘信号", "实盘"],
        "配置分类": "机器人",
    },
    {
        "配置名称": "机器人实盘指标collection名",
        "值": "实盘指标.机器人",
        "配置说明": "机器人实盘指标collection名",
        "配置标签": ["机器人", "实盘指标"],
        "配置分类": "机器人",
    },
    {
        "配置名称": "择时实盘信号collection名",
        "值": "实盘信号.择时装备",
        "配置说明": "择时实盘信号collection名",
        "配置标签": ["择时装备", "实盘信号", "实盘"],
        "配置分类": "装备",
    },
    {
        "配置名称": "选股实盘信号collection名",
        "值": "实盘信号.选股装备",
        "配置说明": "选股实盘信号collection名",
        "配置标签": ["选股装备", "实盘信号", "实盘"],
        "配置分类": "装备",
    },
    {
        "配置名称": "大类资产配置实盘信号collection名",
        "值": "实盘信号.大类资产配置",
        "配置说明": "大类资产配置实盘信号collection名",
        "配置标签": ["大类资产配置", "实盘信号", "实盘"],
        "配置分类": "装备",
    },
    {
        "配置名称": "基金定投实盘信号collection名",
        "值": "实盘信号.基金定投",
        "配置说明": "基金定投实盘信号collection名",
        "配置标签": ["基金定投", "实盘信号", "实盘"],
        "配置分类": "装备",
    },
    {
        "配置名称": "选股实盘指标collection名",
        "值": "实盘指标.选股装备",
        "配置说明": "选股实盘指标collection名",
        "配置标签": ["选股装备", "实盘指标"],
        "配置分类": "装备",
    },
    {
        "配置名称": "择时实盘指标collection名",
        "值": "实盘指标.择时装备",
        "配置说明": "择时实盘指标collection名",
        "配置标签": ["择时装备", "实盘指标"],
        "配置分类": "装备",
    },
    {
        "配置名称": "大类资产配置实盘指标collection名",
        "值": "实盘指标.大类资产配置",
        "配置说明": "大类资产配置实盘指标collection名",
        "配置标签": ["大类资产配置", "实盘指标"],
        "配置分类": "装备",
    },
    {
        "配置名称": "基金定投实盘指标collection名",
        "值": "实盘指标.基金定投",
        "配置说明": "基金定投实盘指标collection名",
        "配置标签": ["基金定投", "实盘指标"],
        "配置分类": "装备",
    },
]

init_role_data = [
    {"name": "免费用户"},
    {"name": "VIP用户"},
    {"name": "超级用户"},
    {"name": "策略管理员"},
    {"name": "厂商用户"},
]

init_permission_data = [
    {
        "role": "免费用户",
        "permissions": {
            "自选股": ["创建", "查看", "修改", "删除"],
            "文章": ["查看", "删除", "修改", "创建"],
            "评论": ["查询", "删除", "修改", "创建"],
            "赞": ["创建", "查看", "修改"],
            "装备": ["查看", "修改", "订阅"],
            "机器人": ["查看", "修改", "订阅"],
            "稻草人数据": ["查看"],
            "包": ["查看", "修改", "订阅"],
            "投资原则": ["查看"],
            "用户": ["查看", "修改"],
            "角色": ["查看"],
            "指标配置": ["查看"],
            "日志": ["创建", "查看", "删除", "修改"],
            "标签": ["查看"],
            "运营数据": ["查看"],
        },
    },
    {"role": "超级用户", "permissions": {"*": ["*"]}},
    {
        "role": "策略管理员",
        "permissions": {
            "策略": ["airflow"],
            "装备": ["查看", "查看他人", "创建", "修改", "修改他人", "删除他人"],
            "机器人": ["查看", "查看他人", "创建", "修改", "修改他人", "删除他人"],
            "稻草人数据": ["查看", "查看他人"],
            "包": ["查看", "查看他人", "创建", "修改", "修改他人"],
            "投资原则": ["查看"],
            "用户": ["查看", "修改"],
            "标签": ["创建", "删除", "查看", "修改"],
            "文章": ["查看", "删除", "修改", "创建"],
        },
    },
    {
        "role": "厂商用户",
        "permissions": {
            "组合": ["创建"],
            "装备": ["查看", "查看他人", "创建", "修改", "订阅"],
            "机器人": ["查看", "查看他人", "创建", "修改", "订阅"],
            "稻草人数据": ["查看"],
            "包": ["查看", "创建", "修改", "订阅"],
            "投资原则": ["查看"],
            "用户": ["查看", "修改"],
            "权限": ["查看"],
            "文章": ["查看", "删除", "修改", "创建"],
            "标签": ["查看"],
            "策略": ["创建", "查询"],
        },
    },
    {
        "role": "VIP用户",
        "permissions": {
            "组合": ["创建", "查看", "修改", "订阅", "取消订阅"],
            "自选股": ["创建", "查看", "修改", "删除"],
            "活动": ["查看"],
            "文章": ["查看", "删除", "修改", "创建"],
            "评论": ["查询", "删除", "修改", "创建"],
            "赞": ["创建", "查看", "修改"],
            "装备": ["查看", "创建", "修改", "订阅"],
            "机器人": ["查看", "创建", "修改", "订阅"],
            "稻草人数据": ["查看"],
            "包": ["查看", "创建", "修改", "订阅"],
            "投资原则": ["查看"],
            "用户": ["查看", "修改"],
            "角色": ["查看"],
            "权限": ["查看"],
            "指标配置": ["查看"],
            "日志": ["创建", "查看", "删除", "修改"],
            "标签": ["创建", "删除", "查看", "修改"],
            "运营数据": ["查看"],
        },
    },
]


async def main(db_name: str, is_init_user: bool = False) -> None:
    """
    Parameters
    ----------
    db_name: 数据库名称
    is_init_user: 是否初始化用户
    """
    database_name = db_name
    logging.debug("连接数据库...\n")
    db = AsyncIOMotorClient(
        settings.db.MONGODB_URL,
        maxPoolSize=settings.db.MAX_CONNECTIONS,
        minPoolSize=settings.db.MIN_CONNECTIONS,
    )
    #############################################################################################################
    # 创建配置集合
    #############################################################################################################
    await create_collection(db[database_name], settings.collections.SITE_CONFIG)
    result = await db[database_name][settings.collections.SITE_CONFIG].create_index("配置名称", unique=True)
    logging.debug(f"创建{result}索引成功。\n")
    try:
        await db[database_name][settings.collections.SITE_CONFIG].insert_many(site_init_configs, ordered=False)
    except BulkWriteError:
        logging.warning(f"插入配置部分成功，如果已有数据请清空数据后再试。如果只是增加配置，可忽略此错误。")
    #############################################################################################################
    #############################################################################################################
    # 创建装备集合
    #############################################################################################################
    try:
        await create_collection(db[database_name], settings.collections.EQUIPMENT)
        result = await db[database_name][settings.collections.EQUIPMENT].create_index("标识符", unique=True)
        logging.debug(f"创建{result}索引成功。\n")
        result = await db[database_name][settings.collections.EQUIPMENT].create_index("名称")
        logging.debug(f"创建{result}索引成功。\n")
        result = await db[database_name][settings.collections.EQUIPMENT].create_index([("标识符", TEXT), ("作者", TEXT), ("名称", TEXT)])
        logging.debug(f"创建{result}索引成功。\n")
        result = await db[database_name][settings.collections.EQUIPMENT].create_index("评级")
        logging.debug(f"创建{result}索引成功。\n")
    except DuplicateKeyError:
        logging.warning(f"装备集合创建部分失败，如果已有数据请清空数据后再试。如果只是增加数据，可忽略此错误。")
    #############################################################################################################
    # 创建机器人集合
    #############################################################################################################
    try:
        await create_collection(db[database_name], settings.collections.ROBOT)
        result = await db[database_name][settings.collections.ROBOT].create_index("标识符", unique=True)
        logging.debug(f"创建{result}索引成功。\n")
        result = await db[database_name][settings.collections.ROBOT].create_index("名称")
        logging.debug(f"创建{result}索引成功。\n")
        result = await db[database_name][settings.collections.ROBOT].create_index([("标识符", TEXT), ("作者", TEXT), ("名称", TEXT)])
        logging.debug(f"创建{result}索引成功。\n")
        result = await db[database_name][settings.collections.ROBOT].create_index("评级")
        logging.debug(f"创建{result}索引成功。\n")
    except DuplicateKeyError:
        logging.warning(f"机器人集合创建部分失败，如果已有数据请清空数据后再试。如果只是增加数据，可忽略此错误。")
    #############################################################################################################
    # 创建角色和权限集合
    #############################################################################################################
    try:
        await db[database_name][settings.collections.ROLE].delete_many({})
        await db[database_name][settings.collections.PERMISSION].delete_many({})
        # 角色数据
        await db[database_name][settings.collections.ROLE].insert_many(init_role_data)
        # 权限数据
        await db[database_name][settings.collections.PERMISSION].insert_many(init_permission_data)
        result = await db[database_name][settings.collections.ROLE].create_index("name", unique=True)
        logging.debug(f"创建{result}索引成功。\n")
        result = await db[database_name][settings.collections.PERMISSION].create_index([("role", ASCENDING)], unique=True)
        logging.debug(f"创建{result}索引成功。\n")
    except BulkWriteError:
        logging.warning(f"插入角色和权限部分成功，如果已有数据请清空数据后再试。如果只是增加数据，可忽略此错误。")
    #############################################################################################################
    # 创建用户集合
    #############################################################################################################
    await create_collection(db[database_name], settings.collections.USER)
    result = await db[database_name][settings.collections.USER].create_index("username", unique=True)
    logging.debug(f"创建{result}索引成功。\n")
    #############################################################################################################
    # 创建 回测实盘表 索引
    #############################################################################################################
    # 回测信号
    await create_collection(db[database_name], "回测信号.选股装备")
    result = await db[database_name]["回测信号.选股装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.选股装备"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测信号.择时装备")
    result = await db[database_name]["回测信号.择时装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.择时装备"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.择时装备"].create_index("标的指数")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测信号.大类资产配置")
    result = await db[database_name]["回测信号.大类资产配置"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.大类资产配置"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测信号.基金定投")
    result = await db[database_name]["回测信号.基金定投"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.基金定投"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测信号.机器人")
    result = await db[database_name]["回测信号.机器人"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.机器人"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.机器人"].create_index("行业分类")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测信号.机器人"].create_index("证券代码")
    logging.debug(f"创建{result}索引成功。\n")

    # 回测指标
    await create_collection(db[database_name], "回测指标.选股装备")
    result = await db[database_name]["回测指标.选股装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测指标.选股装备"].create_index("开始时间")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测指标.选股装备"].create_index("结束时间")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测指标.择时装备")
    result = await db[database_name]["回测指标.择时装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测指标.择时装备"].create_index("回测年份")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测指标.择时装备"].create_index("标的指数")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测指标.大类资产配置")
    result = await db[database_name]["回测指标.大类资产配置"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测指标.大类资产配置"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测指标.基金定投")
    result = await db[database_name]["回测指标.基金定投"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测指标.基金定投"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测指标.机器人")
    result = await db[database_name]["回测指标.机器人"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测指标.机器人"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    # 回测评级
    await create_collection(db[database_name], "回测评级.选股装备")
    result = await db[database_name]["回测评级.选股装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.选股装备"].create_index("数据集")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.选股装备"].create_index("评级")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测评级.择时装备")
    result = await db[database_name]["回测评级.择时装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.择时装备"].create_index("回测年份")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.择时装备"].create_index("标的指数")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.择时装备"].create_index("评级")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测评级.大类资产配置")
    result = await db[database_name]["回测评级.大类资产配置"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.大类资产配置"].create_index("数据集")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.大类资产配置"].create_index("评级")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测评级.基金定投")
    result = await db[database_name]["回测评级.基金定投"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.基金定投"].create_index("数据集")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.基金定投"].create_index("评级")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "回测评级.机器人")
    result = await db[database_name]["回测评级.机器人"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.机器人"].create_index("数据集")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["回测评级.机器人"].create_index("评级")
    logging.debug(f"创建{result}索引成功。\n")

    # 实盘信号
    await create_collection(db[database_name], "实盘信号.选股装备")
    result = await db[database_name]["实盘信号.选股装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.选股装备"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "实盘信号.择时装备")
    result = await db[database_name]["实盘信号.择时装备"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.择时装备"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.择时装备"].create_index("标的指数")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "实盘信号.大类资产配置")
    result = await db[database_name]["实盘信号.大类资产配置"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.大类资产配置"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "实盘信号.基金定投")
    result = await db[database_name]["实盘信号.基金定投"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.基金定投"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "实盘信号.机器人")
    result = await db[database_name]["实盘信号.机器人"].create_index("标识符")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.机器人"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.机器人"].create_index("行业分类")
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘信号.机器人"].create_index("证券代码")
    logging.debug(f"创建{result}索引成功。\n")

    # 实盘指标
    await create_collection(db[database_name], "实盘指标.机器人")
    result = await db[database_name]["实盘指标.机器人"].create_index("标识符", unique=True)
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘指标.机器人"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "实盘指标.大类资产配置")
    result = await db[database_name]["实盘指标.大类资产配置"].create_index("标识符", unique=True)
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘指标.大类资产配置"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")

    await create_collection(db[database_name], "实盘指标.基金定投")
    result = await db[database_name]["实盘指标.基金定投"].create_index("标识符", unique=True)
    logging.debug(f"创建{result}索引成功。\n")
    result = await db[database_name]["实盘指标.基金定投"].create_index("交易日期")
    logging.debug(f"创建{result}索引成功。\n")
    if is_init_user:
        #############################################################################################################
        #############################################################################################################
        # 创建策略管理员
        #############################################################################################################
        try:
            airflow_user_mobile = input("请输入策略管理员的mobile:")
            user = UserInCreate(
                username=airflow_user_mobile,
                password="JinChongZi321",
                mobile=airflow_user_mobile,
            )
            await create_user(db, user, "策略管理员")
            logging.debug(f"创建策略管理员成功！\n")
        except DuplicateKeyError as e:
            logging.warning(f"创建策略管理员失败，请先清空数据后再试！{e}")
        #############################################################################################################
        # 创建超级用户
        #############################################################################################################
        try:
            print("系统基础配置已经完成，接下来系统将会帮助您创建超级用户管理员。")
            root_user_mobile = input("请输入超级用户的mobile:")
            root_user_pass = getpass.getpass("请输入超级用户的密码:")
            user = UserInCreate(
                username=root_user_mobile,
                password=root_user_pass,
                mobile=root_user_mobile,
            )
            await create_user(db, user, "超级用户")
            logging.debug(f"创建超级用户成功，可以尝试使用超级用户开始工作了！\n")
        except DuplicateKeyError as e:
            logging.warning(f"创建用户失败，请先清空数据后再试！{e}")


if __name__ == "__main__":
    answer = input("有可能引起数据丢失，你确定要初始化数据吗？(Y/N)")
    if answer == "Y" or answer == "y":
        logging.basicConfig(level=logging.DEBUG)
        asyncio.run(main(settings.db.DB_NAME, is_init_user=True))
        print("初始化完成！")
    else:
        print("很好，下次想好了再来！")
