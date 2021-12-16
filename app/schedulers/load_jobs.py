from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app import settings
from app.core.scheduler import BeehiveMongoDBJobStore, log_listener
from app.extentions import logger
from app.schedulers import scheduler
from app.schedulers.add_jobs import add_jobs


async def load_jobs():
    """加载定时任务"""
    init_scheduler_options = {
        "jobstores": {
            "default": BeehiveMongoDBJobStore(
                collection="job",
                database=settings.db.DB_NAME,
                client=settings.db.get_client()
            )
        },
    }
    scheduler.configure(**init_scheduler_options)
    # 增加日志监听器
    scheduler.add_listener(log_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    logger.info("开始加载定时任务...")
    await add_jobs(scheduler)
    logger.info("加载定时任务完毕!")

    logger.info("启动定时任务...")
    scheduler.start()
    logger.info("启动定时任务完毕！")


async def load_jobs_with_lock():
    """加载定时任务：增加文件锁，限制同一时间内只有一个进程可以操作定时任务"""
    try:
        import atexit
        import fcntl
    except ImportError:
        await load_jobs()
    else:
        f = open("scheduler.lock", "wb")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            await load_jobs()
        except Exception as e:
            pass

        def unlock():
            fcntl.flock(f, fcntl.LOCK_UN)
            f.close()

        atexit.register(unlock)
