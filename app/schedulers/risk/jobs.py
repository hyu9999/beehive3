from app import settings
from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.risk.config import risk_detection_with_condition_config, preload_robot_data_config


class RiskJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, risk_detection_with_condition_config)
        JobTools.add_base(scheduler, preload_robot_data_config, settings.scheduler.max_thread_num)

    @classmethod
    def mfrs(cls, *args):
        pass
