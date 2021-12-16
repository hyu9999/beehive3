from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.portfolio.config import update_portfolio_profit_rank_data_config


class PortfolioJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, update_portfolio_profit_rank_data_config)

    @classmethod
    def mfrs(cls, *args):
        pass
