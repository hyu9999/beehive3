from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage

from app import settings
from app.outer_sys.message.adaptor.base import SendAdaptor


class SendWechatMessage(SendAdaptor):
    """发送微信消息"""

    def send_code(self, *args, **kwargs):
        pass

    def __init__(self):
        self.app_id = settings.wechat.app_id
        self.app_secret = settings.wechat.app_secret
        self.client = self._client()

    def _client(self):
        wechat_client = WeChatClient(appid=self.app_id, secret=self.app_secret)
        client = WeChatMessage(wechat_client)
        return client

    def send(self, *, content: str, open_id: str):
        try:
            data = self.client.send_text(open_id, content)
        except WeChatClientException as e:
            data = {k: v for k, v in zip(["errcode", "errmsg"], e.args)}
        return self.format_return_message(data)

    def format_return_message(self, data):
        return {k: v for (old_k, v), k in zip(data.items(), ["code", "error_message"])}
