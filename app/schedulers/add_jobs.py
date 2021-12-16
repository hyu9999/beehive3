from app.schedulers.ability.jobs import AbilityDataJobs
from app.schedulers.activity.jobs import ActivityJobs
from app.schedulers.cn_collection.jobs import CnCollectionJobs
from app.schedulers.disc.jobs import DiscJobs
from app.schedulers.init_sys.jobs import InitSystemJobs
from app.schedulers.liquidation.jobs import LiquidationJobs
from app.schedulers.message.jobs import MessageJobs
from app.schedulers.operation_data.jobs import OperationJobs
from app.schedulers.order.jobs import OrderJobs
from app.schedulers.portfolio.jobs import PortfolioJobs
from app.schedulers.publish.jobs import PublishJobs
from app.schedulers.risk.jobs import RiskJobs
from app.schedulers.stock.jobs import StockJobs
from app.schedulers.time_series_data.jobs import TimeSeriesDataJobs
from app.schedulers.wechat.jobs import WechatJobs
from app.schedulers.zvt_data_log.jobs import ZvtDataLogJobs


# TODO 如何动态加载定时任务jobs
def get_job_objs():
    return [
        ActivityJobs,
        DiscJobs,
        InitSystemJobs,
        MessageJobs,
        OperationJobs,
        OrderJobs,
        PortfolioJobs,
        RiskJobs,
        WechatJobs,
        PublishJobs,
        ZvtDataLogJobs,
        CnCollectionJobs,
        StockJobs,
        TimeSeriesDataJobs,
        AbilityDataJobs,
        LiquidationJobs,
    ]


async def add_jobs(scheduler):
    """添加定时任务"""
    job_objs = get_job_objs()
    for i in job_objs:
        i.add(scheduler)
