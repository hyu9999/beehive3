from abc import ABC, abstractmethod


class SendAdaptor(ABC):
    """消息发送适配器"""

    @abstractmethod
    def send(self, *args, **kwargs):
        """
        消息发送函数

        Parameters
        ----------

        Returns
        -------

        """
        pass

    @abstractmethod
    def send_code(self, *args, **kwargs):
        """
        验证码发送函数

        Parameters
        ----------

        Returns
        -------

        """
        pass

    @abstractmethod
    def format_return_message(self, *args, **kwargs):
        pass
