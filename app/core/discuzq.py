from typing import Dict

from app import settings
from app.core.discuzqlib.client import DiscuzqClient


class Discuzq:
    clients: Dict[str, DiscuzqClient] = {}
    _admin: DiscuzqClient = None

    @classmethod
    def client(cls, username=None, password=None):
        """获取discourse的client"""
        cl = cls.clients.get(
            username, DiscuzqClient(settings.discuzq.base_url, username, password)
        )
        cls.clients[username] = cl
        return cl

    @classmethod
    def admin(cls):
        if cls._admin is None:
            cls._admin = DiscuzqClient(
                settings.discuzq.base_url,
                settings.discuzq.admin,
                settings.discuzq.password,
            )
        return cls._admin
