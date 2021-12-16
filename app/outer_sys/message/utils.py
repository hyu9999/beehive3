import random

from app import settings
from app.core.errors import LoginError
from app.global_var import G


def verification_code():
    """
    生成6位随意验证码

    Returns
    -------

    """
    code = random.randint(100000, 999999)
    return code


async def verify_code(mobile: str, code: str):
    """
    校验短信验证码

    Parameters
    ----------
    mobile
    code

    Returns
    -------

    """
    if settings.sms.switch:
        redis_value = await G.cache.get(f"sms_{mobile}")
        if not redis_value:
            raise LoginError(message="验证码过期失效")
        if redis_value and redis_value != code:
            raise LoginError(message="验证码错误")
    else:
        if settings.sms.fixed_code != code:
            raise LoginError(message="验证码错误")
    return True
