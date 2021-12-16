from pydantic import Field
from fastapi_plugins import SchedulerSettings as BaseSchedulerSettings

from app.settings import OtherSettings


class SchedulerSettings(OtherSettings, BaseSchedulerSettings):
    max_thread_num: int = Field(..., description="定时任务异步任务最大线程数", env="scheduler_max_thread_num")
