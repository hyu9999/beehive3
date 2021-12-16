from pydantic import Field

from app.settings import OtherSettings


class LogSettings(OtherSettings):
    log_level: str = Field(..., env="LOG_LEVEL")  #
    task_log_level: str = Field(..., env="TASK_LOG_LEVEL")  #
    websockets_log_level: str = Field(..., env="WEBSOCKETS_LOG_LEVEL")  #
    uvicorn_access_log_level: str = Field(..., env="UVICORN_ACCESS_LOG_LEVEL")  #
    root_log_level: str = Field(..., env="ROOT_LOG_LEVEL")  #
