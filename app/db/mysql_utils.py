from stralib.mysql import MySQLBase

from app import settings
from app.extentions import logger
from app.global_var import G


async def init_mysql():
    """初始化mysql数据库"""
    try:
        logger.info("连接行情数据库中...")
        G.hq_mysql = MySQLBase(
            db=settings.hq.db_name, host=settings.hq.db_host, port=settings.hq.db_port, user=settings.hq.db_username, passwd=settings.hq.db_password,
        )
        logger.info("连接行情数据库成功！")
    except ConnectionRefusedError as e:
        logger.info(f"连接mysql数据库错误：{e}")
        return


async def close_mysql():
    """关闭mysql数据库"""
    logger.info("关闭mysql数据库连接...")
    G.hq_mysql.close()
    logger.info("mysql数据库连接关闭！")
