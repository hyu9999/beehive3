from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.init_sys.config import (
    place_order_onstart_config,
    check_order_onstart_config,
    update_portfolio_profit_rank_data_onstart_config, update_strategy_calculate_datetime_onstart_config,
)


class InitSystemJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(scheduler, place_order_onstart_config)
        JobTools.add_base(scheduler, check_order_onstart_config)
        JobTools.add_base(scheduler, update_portfolio_profit_rank_data_onstart_config)
        JobTools.add_base(scheduler, update_strategy_calculate_datetime_onstart_config)

    @classmethod
    def mfrs(cls, *args):
        pass
