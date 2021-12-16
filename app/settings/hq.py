from pydantic import Field

from app.settings import OtherSettings


class HQSettings(OtherSettings):
    source: str = Field(..., description="行情源", env="HQ_SOURCE")

    db_name: str = Field(..., description="行情数据库名称", env="HQDB_NAME")
    db_host: str = Field(..., description="行情数据库ip", env="HQDB_HOST")
    db_port: int = Field(..., description="行情数据库端口", env="HQDB_PORT")
    db_username: str = Field(..., description="行情数据库用户名", env="HQDB_USERNAME")
    db_password: str = Field(..., description="行情数据库密码", env="HQDB_PASSWORD")
    hq_url: str = Field(..., description="接口调用行情时的地址", env="HQ_URL")
    jiantou_url: str = Field(..., description="建投URL", env="JIANTOU_URL")
    refresh_interval_seconds: int = Field(..., description="行情刷新时间间隔")
