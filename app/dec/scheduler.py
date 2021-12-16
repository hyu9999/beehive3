from functools import wraps
from time import time

from app.schedulers import logger


def print_execute_time(func):

    # 定义嵌套函数，用来打印出装饰的函数的执行时间
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 定义开始时间和结束时间，将func夹在中间执行，取得其返回值
        start = time()
        logger.info(f"【start】{func.__name__}")
        func_return = await func(*args, **kwargs)
        end = time()
        logger.info(f"【end】{func.__name__}_{end - start}s")
        # 返回func的返回值
        return func_return

    # 返回嵌套的函数
    return wrapper
