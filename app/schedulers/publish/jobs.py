from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.publish.config import write_strategy_publish_log_config, check_strategy_data_task_config


class PublishJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, write_strategy_publish_log_config)
        # JobTools.add_base(scheduler, check_strategy_data_task_config)

    @classmethod
    def mfrs(cls, *args):
        pass
