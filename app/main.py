from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import settings
from app.api.api_v1.api import router as api_router
from app.core.regiser import register_exceptions
from app.db.mongodb_utils import (
    close_mongo_connection,
    connect_to_mongo,
    load_configuration_from_mongo,
)
from app.db.mysql_utils import close_mysql, init_mysql
from app.db.redis_utils import close_redis, init_redis_pool
from app.extentions.logger import init_log
from app.middleware import DBErrorMiddleware
from app.outer_sys.hq.events import close_hq2redis_conn, connect_hq2reids, set_hq_source
from app.outer_sys.trade_system import close_trade_system, connect_trade_system
from app.outer_sys.wechat.utils import init_wechat
from app.schedulers.load_jobs import load_jobs_with_lock

init_log()


app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
)

app.add_middleware(DBErrorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("startup", load_configuration_from_mongo)
app.add_event_handler("startup", load_jobs_with_lock)
app.add_event_handler("startup", set_hq_source)
app.add_event_handler("shutdown", close_mongo_connection)
if not settings.manufacturer_switch:
    app.add_event_handler("startup", init_redis_pool)
    app.add_event_handler("startup", connect_hq2reids)
    app.add_event_handler("shutdown", close_hq2redis_conn)
    app.add_event_handler("startup", connect_trade_system)
    app.add_event_handler("startup", init_mysql)
    app.add_event_handler("startup", init_wechat)
    app.add_event_handler("shutdown", close_redis)
    app.add_event_handler("shutdown", close_mysql)
    app.add_event_handler("shutdown", close_trade_system)

register_exceptions(app)  # 注册异常
app.include_router(api_router, prefix=settings.url_prefix)
