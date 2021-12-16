from functools import wraps
from app import settings


def disc_switch_decor(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if settings.discuzq.switch:
            return await func(*args, **kwargs)
        else:
            return None
    return wrapper
