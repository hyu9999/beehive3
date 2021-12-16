import logging
import sys
from logging.config import dictConfig
from os import makedirs
from os.path import dirname, exists

from app import settings


def init_log():
    log_config = {
        "version": 1,
        "formatters": {
            "default": {"format": "[%(asctime)s][%(name)s] %(levelname)s:%(message)s"},
            "scheduler": {"format": "[%(asctime)s][scheduler] %(levelname)s:%(message)s"},
            "standard": {"format": "[%(asctime)s][%(name)s] %(levelname)s:%(message)s - [%(pathname)s:%(lineno)d]"},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "standard"},
            "scheduler": {"class": "logging.StreamHandler", "formatter": "scheduler"},
        },
        "loggers": {
            "beehive3": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "fastapi": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "fastapi.beehive.log": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "apscheduler": {"level": settings.TASK_LOG_LEVEL, "handlers": ["scheduler"], "propagate": False},
            "websockets": {"level": settings.WEBSOCKETS_LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "uvicorn": {"level": settings.UVICORN_ACCESS_LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "gunicorn": {"level": settings.UVICORN_ACCESS_LOG_LEVEL, "handlers": ["console"], "propagate": False},
        },
        "root": {"level": settings.ROOT_LOG_LEVEL, "handlers": ["console"]},
    }
    dictConfig(log_config)


loggers = {}


def get_logger(name=None):
    """
    get logger by name

    Parameters
    ----------
    name: name of logger

    Returns
    -------
    logger
    """
    global loggers

    if not name:
        name = __name__

    if loggers.get(name):
        return loggers.get(name)

    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)

    # 输出到控制台
    if settings.LOG_ENABLED and settings.LOG_TO_CONSOLE:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level=settings.LOG_LEVEL)
        formatter = logging.Formatter(settings.LOG_FORMAT)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # 输出到文件
    if settings.LOG_ENABLED and settings.LOG_TO_FILE:
        # 如果路径不存在，创建日志文件文件夹
        log_dir = dirname(settings.LOG_PATH)
        if not exists(log_dir):
            makedirs(log_dir)
        # 添加 FileHandler
        file_handler = logging.FileHandler(settings.LOG_PATH, encoding="utf-8")
        file_handler.setLevel(level=settings.LOG_LEVEL)
        formatter = logging.Formatter(settings.LOG_FORMAT)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 保存到全局 loggers
    loggers[name] = logger
    return logger
