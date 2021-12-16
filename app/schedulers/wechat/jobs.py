from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.wechat.config import sync_wechat_avatar_config


class WechatJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, sync_wechat_avatar_config)

    @classmethod
    def mfrs(cls, *args):
        pass
