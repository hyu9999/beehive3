from abc import ABCMeta, abstractmethod

from app import settings


class JobTools:
    @classmethod
    def add_base(cls, scheduler, config, job_num=None):
        """任务生成"""
        if job_num:
            for i in range(0, job_num):
                func = config.get("func")
                scheduler.add_job(func, id=f"{func.__name__}_{i}", args=(i, job_num), **config.get("cron"))
        else:
            scheduler.add_job(config.get("func"), **config.get("cron"))


class JobAbs(metaclass=ABCMeta):
    """定时任务添加job抽象类"""

    @classmethod
    @abstractmethod
    def common(cls, *args, **kwargs):
        """公共定时任务"""

    @classmethod
    @abstractmethod
    def master(cls, *args, **kwargs):
        """主分支定时任务"""

    @classmethod
    @abstractmethod
    def mfrs(cls, *args, **kwargs):
        """厂商定时任务"""

    @classmethod
    def add(cls, *args, **kwargs):
        """增加jobs"""
        cls.common(*args, **kwargs)
        if settings.manufacturer_switch:
            cls.mfrs(*args, **kwargs)
        else:
            cls.master(*args, **kwargs)
