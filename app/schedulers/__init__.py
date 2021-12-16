import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("apscheduler.scheduler")


scheduler = AsyncIOScheduler()
