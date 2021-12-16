from typing import List, Dict

from pydantic import Field

from app.settings import OtherSettings


class DiscuzqSettings(OtherSettings):
    base_url: str = Field(..., env="discuzq_base_url")  # 社区url
    admin: str = Field(..., env="discuzq_admin")
    password: str = Field(..., env="discuzq_password")
    switch: str = Field(..., env="discuzq_switch") # 社区启用开关
    category: Dict[str, int] = Field(..., env="discuzq_category")

