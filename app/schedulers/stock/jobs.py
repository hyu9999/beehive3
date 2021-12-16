from app.schedulers.base.job_utils import JobAbs, JobTools
from app.schedulers.stock.config import update_stock_info_config


class StockJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        ...

    @classmethod
    def master(cls, scheduler):
        ...

    @classmethod
    def mfrs(cls, scheduler):
        JobTools.add_base(scheduler, update_stock_info_config)
