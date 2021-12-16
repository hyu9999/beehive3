from app.schedulers.activity.config import activity_online_task_config, activity_finished_task_config
from app.schedulers.base.job_utils import JobTools, JobAbs


class ActivityJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, activity_online_task_config)
        JobTools.add_base(scheduler, activity_finished_task_config)

    @classmethod
    def mfrs(cls, *args):
        pass
