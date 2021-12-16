from pydantic import Field

from app.core.security import generate_salt, get_password_hash, verify_password
from app.enums.user import 用户状态
from app.models.base.user import 厂商基本信息, 用户基本信息, 用户消息基本信息
from app.models.dbmodel import DBModelMixin


class User(DBModelMixin, 用户基本信息):
    """用户表"""

    client_name: str = Field(None, title="厂商名称")
    client: 厂商基本信息 = Field(厂商基本信息(), title="厂商用户")
    app_secret: str = Field(None, title="厂商用户app_secret")
    status: 用户状态 = Field(用户状态.normal, title="状态")
    salt: str = ""
    hashed_password: str = ""

    def check_password(self, password: str):
        return verify_password(self.salt + password, self.hashed_password)

    def change_password(self, password: str):
        self.salt = generate_salt()
        self.hashed_password = get_password_hash(self.salt + password)

    def check_app_secret(self, app_secret: str):
        return verify_password(self.salt + app_secret, self.app_secret)

    def change_app_secret(self, app_secret: str):
        self.app_secret = get_password_hash(self.salt + app_secret)


class UserMessage(DBModelMixin, 用户消息基本信息):
    """用户消息"""
