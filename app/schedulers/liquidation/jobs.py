from app.schedulers.base.job_utils import JobAbs, JobTools
from app.schedulers.liquidation.config import (
    liquidate_dividend_config,
    liquidate_dividend_flow_config,
    liquidate_dividend_tax_config
)


class LiquidationJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, liquidate_dividend_config)
        JobTools.add_base(scheduler, liquidate_dividend_flow_config)
        JobTools.add_base(scheduler, liquidate_dividend_tax_config)

    @classmethod
    def mfrs(cls, *args):
        pass
