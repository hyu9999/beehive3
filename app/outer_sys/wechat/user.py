from wechatpy import WeChatClientException

from app.extentions import logger
from app.global_var import G


def get_wechat_avatar(open_id):
    """
    获取微信头像
    Parameters
    ----------
    open_id

    Returns
    -------

    """

    try:
        wx_user = G.wechat_client.user.get(open_id) if open_id else None
    except WeChatClientException as e:
        logger.error(f"获取用户微信头像失败：{e}")
        avatar = ""
    else:
        avatar = wx_user.get("headimgurl") if wx_user else ""
    return avatar
