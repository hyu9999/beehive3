from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.operation_data.config import update_strategy_calculate_datetime_config, update_operation_data_config


class OperationJobs(JobAbs):
    @classmethod
    def common(cls, scheduler):
        JobTools.add_base(scheduler, update_strategy_calculate_datetime_config)

    @classmethod
    def master(cls, scheduler):
        ...

    @classmethod
    def mfrs(cls, scheduler):
        JobTools.add_base(scheduler, update_operation_data_config)
