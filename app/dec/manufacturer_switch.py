from functools import wraps

from app import settings


def permission_check_decor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if settings.manufacturer_switch:
            return func(*args, **kwargs)

    return wrapper


def equipment_op_decor(err):
    def inner(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if settings.manufacturer_switch:
                raise err()
            else:
                return await func(*args, **kwargs)

        return wrapper

    return inner
