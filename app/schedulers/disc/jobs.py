from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.disc.config import fill_disc_data_config


class DiscJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, fill_disc_data_config)

    @classmethod
    def mfrs(cls, *args):
        pass

