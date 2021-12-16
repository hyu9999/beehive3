from app.schedulers.ability.config import (
    calculate_manual_import_portfolio_ability_config,
    calculate_simulated_trading_portfolio_ability_config,
)
from app.schedulers.base.job_utils import JobAbs, JobTools


class AbilityDataJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        ...

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(
            scheduler, calculate_simulated_trading_portfolio_ability_config
        )
        JobTools.add_base(scheduler, calculate_manual_import_portfolio_ability_config)

    @classmethod
    def mfrs(cls, *args):
        ...
