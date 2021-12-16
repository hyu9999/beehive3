import asyncio
import pickle
from datetime import datetime

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.util import datetime_to_utc_timestamp, maybe_ref
from bson import Binary
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from app import settings
from app.db.mongodb import db

"""
定时任务: job存储器
"""


class BeehiveMongoDBJobStore(MongoDBJobStore):
    """mongodb job存储器"""

    def __init__(self, database="apscheduler", collection="jobs", client=None, pickle_protocol=pickle.HIGHEST_PROTOCOL, **connect_args):
        super(BeehiveMongoDBJobStore, self).__init__()
        self.pickle_protocol = pickle_protocol

        if not database:
            raise ValueError('The "database" parameter must not be empty')
        if not collection:
            raise ValueError('The "collection" parameter must not be empty')

        if client:
            self.client = maybe_ref(client)
        else:
            connect_args.setdefault("w", 1)
            self.client = MongoClient(**connect_args)

        self.collection = self.client[database][collection]

    def add_job(self, job):
        try:
            self.collection.insert(
                {
                    "_id": job.id,
                    "next_run_time": datetime_to_utc_timestamp(job.next_run_time),
                    "job_state": Binary(pickle.dumps(job.__getstate__(), self.pickle_protocol)),
                }
            )
        except DuplicateKeyError:
            raise ConflictingIdError(job.id)

    def update_job(self, job):
        changes = {"next_run_time": datetime_to_utc_timestamp(job.next_run_time), "job_state": Binary(pickle.dumps(job.__getstate__(), self.pickle_protocol))}
        result = self.collection.update({"_id": job.id}, {"$set": changes})
        if result and result["n"] == 0:
            raise JobLookupError(job.id)

    def remove_job(self, job_id):
        result = self.collection.remove(job_id)
        if result and result["n"] == 0:
            raise JobLookupError(job_id)

    def remove_all_jobs(self):
        self.collection.remove()


"""
定时任务: 监听器
"""


def log_listener(event):
    """日志监听"""
    from app.schedulers import scheduler

    func_name = scheduler.get_job(event.job_id).name
    if event.exception:
        status = "failed"
        msg = f"Error: {event.exception.args}"
        detail = event.traceback.split("\n")
    else:
        status = "success"
        msg = "Success"
        detail = None
    params = {"job_id": event.job_id, "func_name": func_name, "status": status, "message": msg, "detail": detail, "create_at": datetime.utcnow()}
    asyncio.ensure_future(add_job_log(**params))


"""
辅助函数
"""


async def add_job_log(*, job_id=None, func_name=None, status=None, message=None, detail=None, create_at=None):
    """
    创建job日志

    Parameters
    ----------
    job_id    job唯一标识
    func_name job函数
    status    状态
    message   信息
    detail    详情
    create_at 创建日期

    Returns
    -------

    """
    params = {"job_id": job_id, "func_name": func_name, "status": status, "message": message, "detail": detail, "create_at": datetime.utcnow()}
    db.client[settings.db.DB_NAME]["job_log"].insert_one(params)
