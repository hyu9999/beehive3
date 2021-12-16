from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage

from app import settings
from app.extentions import logger
from app.global_var import G


async def init_wechat():
    logger.info("初始化微信...")
    G.wechat_client = WeChatClient(appid=settings.wechat.app_id, secret=settings.wechat.app_secret)
    G.msg_client = WeChatMessage(G.wechat_client)
    logger.info("初始化微信成功...")
