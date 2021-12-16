from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.order.config import close_order_config, place_order_config, check_order_config


class OrderJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, close_order_config)
        JobTools.add_base(scheduler, place_order_config)
        JobTools.add_base(scheduler, check_order_config)

    @classmethod
    def mfrs(cls, *args):
        pass
