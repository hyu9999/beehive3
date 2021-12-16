from app.schedulers.base.job_utils import JobAbs, JobTools
from app.schedulers.time_series_data.config import (
    liquidation_fund_asset_config,
    save_manual_import_portfolio_time_series_data_config,
    save_simulated_trading_portfolio_time_series_data_config,
    sync_time_series_data_config, save_manual_import_portfolio_time_series_data_config2,
)


class TimeSeriesDataJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        ...

    @classmethod
    def master(cls, scheduler):
        JobTools.add_base(
            scheduler, save_simulated_trading_portfolio_time_series_data_config
        )
        JobTools.add_base(
            scheduler, save_manual_import_portfolio_time_series_data_config
        )
        JobTools.add_base(
            scheduler, save_manual_import_portfolio_time_series_data_config2
        )
        JobTools.add_base(scheduler, liquidation_fund_asset_config)
        # 需要同步全部历史时点数据时取消注释
        # JobTools.add_base(scheduler, sync_time_series_data_config)

    @classmethod
    def mfrs(cls, *args):
        ...
