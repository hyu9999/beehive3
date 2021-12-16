from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.cn_collection.config import increment_update_cn_collection_data_config, added_missing_real_collection_data_config


class CnCollectionJobs(JobAbs):
    @classmethod
    def common(cls, *args, **kwargs):
        pass

    @classmethod
    def master(cls, *args, **kwargs):
        pass

    @classmethod
    def mfrs(cls, scheduler):
        JobTools.add_base(scheduler, increment_update_cn_collection_data_config)
        JobTools.add_base(scheduler, added_missing_real_collection_data_config)
