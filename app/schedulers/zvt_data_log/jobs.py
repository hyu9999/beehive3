from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.zvt_data_log.config import reset_zvt_data_log_state_config


class ZvtDataLogJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, reset_zvt_data_log_state_config)

    @classmethod
    def mfrs(cls, *args):
        pass
