import os
from datetime import time
from functools import lru_cache
from typing import Optional, Dict

from pydantic import Field

from app.settings import OtherSettings
from app.settings.airflow import AirflowSettings
from app.settings.auth import WebAuth, PWDWebAuth
from app.settings.db import DbSettings, Collections
from app.settings.discuzq import DiscuzqSettings
from app.settings.hq import HQSettings
from app.settings.log import LogSettings
from app.settings.message import SMSSettings, EmailSettings, WechatSettings
from app.settings.mfrs import MfrsSettings
from app.settings.redis import RedisSettings
from app.settings.scheduler import SchedulerSettings


class GlobalConfig(OtherSettings):
    ENV_STATE: str = Field(..., description="环境配置", env="ENV_STATE")
    # 项目基本信息
    version: str = Field(..., description="项目版本", env="version")
    project_name: str = Field(..., description="项目名称", env="project_name")
    description: str = Field(..., description="项目描述", env="description")
    secret_key: str = Field(..., description="项目密钥", env="secret_key")
    allowed_hosts: list = Field(..., description="host可访问列表", env="allowed_hosts")
    debug: bool = Field(..., description="是否是debug模式", env="debug")
    url_prefix: str = Field(..., description="url前缀", env="url_prefix")
    access_token_expire_minutes: int = Field(..., description="token过期时间", env="access_token_expire_minutes")
    calculation_completion_time_point: int = Field(..., description="数据计算完毕时间点", env="calculation_completion_time_point")
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    manufacturer_switch: bool = Field(..., description="厂商开关", env="MANUFACTURER_SWITCH")
    # 交易系统
    trade_url: str = Field(..., description="模拟交易系统url", env="trade_url")
    market_index_list: list = Field(..., description="市场指数", env="market_index_list")
    host: str = Field(..., description="HOST", env="beehive3_host")
    port: str = Field(..., description="PORT", env="beehive3_port")
    vip_code: str = Field(..., description="vip验证码")
    open_market_time: time = Field(..., description="开市时间")
    close_market_time: time = Field(..., description="闭市时间")
    allow_pending_order_time: time = Field(..., description="允许挂单时间")
    commission: float = Field(..., description="佣金")
    tax: float = Field(..., description="税点")

    db: DbSettings = DbSettings()
    collections: Collections = Collections()
    redis: RedisSettings = RedisSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    discuzq: DiscuzqSettings = DiscuzqSettings()
    airflow: AirflowSettings = AirflowSettings()
    log: LogSettings = LogSettings()
    hq: HQSettings = HQSettings()
    mfrs: MfrsSettings = MfrsSettings()
    wechat: WechatSettings = WechatSettings()
    sms: SMSSettings = SMSSettings()
    email: EmailSettings = EmailSettings()

    # 登录认证
    auth: WebAuth = PWDWebAuth()
    # 权限设置
    num_limit: Dict[str, Dict[str, int]] = Field(..., description="角色可创建数量限制（包含组合、装备、机器人等）", env="num_limit")
    # 聚宽登陆
    jqdata_user: str = Field(..., description="聚宽账号", env="jqdata_user")
    jqdata_password: str = Field(..., description="聚宽密码", env="jqdata_password")
    jqdata_url: str = Field(..., description="聚宽API接口", env="jqdata_url")
    # log
    LOG_ENABLED: bool = Field(..., description="是否开启日志", env="LOG_ENABLED")
    LOG_TO_CONSOLE: bool = Field(..., description="是否输出到控制台", env="LOG_TO_CONSOLE")
    LOG_TO_FILE: bool = Field(..., description="是否输出到文件", env="LOG_TO_FILE")
    LOG_FORMAT: str = Field(..., description="日志打印格式", env="LOG_FORMAT")
    LOG_PATH: str = Field(..., description="日志文件存放路径", env="LOG_PATH")

    LOG_LEVEL: str = Field(..., description="项目日志打印级别", env="LOG_LEVEL")
    TASK_LOG_LEVEL: str = Field(..., description="项目日志打印级别", env="TASK_LOG_LEVEL")
    WEBSOCKETS_LOG_LEVEL: str = Field(..., description="项目日志打印级别", env="WEBSOCKETS_LOG_LEVEL")
    UVICORN_ACCESS_LOG_LEVEL: str = Field(..., description="项目日志打印级别", env="UVICORN_ACCESS_LOG_LEVEL")
    ROOT_LOG_LEVEL: str = Field(..., description="项目日志打印级别", env="ROOT_LOG_LEVEL")


class DevConfig(GlobalConfig):
    """Development configurations."""


class ProdConfig(GlobalConfig):
    """Production configurations."""

    class Config:
        env_prefix: str = "PROD_"


class FactoryConfig:
    """Returns a config instance dependending on the ENV_STATE variable."""

    def __init__(self, env_state: Optional[str]):
        self.env_state = env_state

    def __call__(self):
        if self.env_state.upper() == "DEV":
            return DevConfig()

        elif self.env_state.upper() == "PROD":
            return ProdConfig()


@lru_cache()
def get_settings():
    return FactoryConfig(GlobalConfig().ENV_STATE)()
