from app.outer_sys.message.adaptor.base import SendAdaptor


class SendMessage:
    """消息发送类"""

    def __init__(self, adaptor: SendAdaptor):
        self.adaptor = adaptor

    def send(self, **kwargs):
        """
        发送函数

        Parameters
        ----------

        Returns
        -------

        """
        self.adaptor.send(**kwargs)

    def send_code(self, **kwargs):
        """
        发送验证码函数

        Parameters
        ----------

        Returns
        -------

        """
        return self.adaptor.send_code(**kwargs)
