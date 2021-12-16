from fastapi_plugins import RedisSettings as BaseRedisSettings
from fastapi_plugins import RedisType
from pydantic import Field

from app.settings import OtherSettings


class RedisSettings(OtherSettings, BaseRedisSettings):
    redis_type: RedisType = RedisType.redis
    #
    redis_url: str
    redis_host: str
    redis_port: int
    redis_password: str = ""
    redis_connection_timeout: int

    # hq2redis
    hq2redis_host: str
    hq2redis_port: int
    hq2redis_password: str
    hq2redis_db: str

    redis_pool_minsize: int
    redis_pool_maxsize: int
    default_time_out: int = Field(..., description="默认超时时间", env="default_time_out")
    # 数据库
    cache_db: int  # 缓存库
    entrust_db: int  # 存储委托订单
    portfolio_yield_db: int  # 组合收益率排行信息
    scheduler_db: int  # 定时任务临时变量
    preload_db: int  # 预加载数据

    def get_redis_address(self, db: int = None) -> str:
        db = db or self.cache_db
        return (
            f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{db}"
        )
