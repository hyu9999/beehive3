from pydantic import Field
from typing import List

from app.settings import OtherSettings


class MfrsSettings(OtherSettings):
    BEEHIVE_URL: str = Field(..., description="beehive3地址", env="BEEHIVE_URL")
    CLIENT_USER: str = Field(..., description="厂商用户名", env="CLIENT_USER")
    APP_SECRET: str = Field(..., description="厂商秘钥", env="APP_SECRET")
    CLIENT_INDICATOR: List[str] = Field(..., description="策略运行所需要的ATR指标")
