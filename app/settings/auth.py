from jwt.algorithms import RSAAlgorithm
from pydantic import Field

from app.settings import OtherSettings


class BaseAuth(OtherSettings):
    """认证基类"""

    audience: str = None
    public_key: str = None
    algorithm: list = None

    api_key: str = Field(..., description="后管api_key，用于校验后台登录", env="api_key")

    def get_rsa_public_key(self):
        return self.public_key


class WebAuth(BaseAuth):
    """前台认证"""

    jwt_token_prefix: str = Field(..., description="token前缀", env="web_jwt_token_prefix")
    base_url: str = Field(..., description="前端url地址", env="web_base_url")


class PWDWebAuth(WebAuth):
    # 加密
    audience: str = Field(..., env="web_audience")
    public_key: str = Field(..., env="web_public_key")
    access_token_jwt_subject: str = Field(..., env="web_access_token_jwt_subject")
    algorithm: list = Field(..., env="web_algorithm")

    def get_rsa_public_key(self):
        return self.public_key
