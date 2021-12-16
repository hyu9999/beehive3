import calendar
from datetime import datetime, date
from typing import Union, Iterable

from stralib import FastTdate

from app import settings

SIX_HOUR = 6 * 60 * 60
DAY = 24 * 60 * 60
WEEK = 7 * DAY
UPDATE_ACCOUNT_TIME = 151000


def get_early_morning(dt: datetime = None) -> datetime:
    """
    获取指定日期的凌晨时间，默认当天(UTC时间)
    Parameters
    ----------
    dt 指定日期
    Returns
    -------
    datetime
    """
    dt = dt or datetime.utcnow()
    early_dt = datetime(dt.year, dt.month, dt.day)
    return early_dt


def get_exist_signal_date(end_date: datetime) -> datetime:
    """
    根据传入日期获取实际存在策略信号日期

    如果传入日期不是交易日，则取上一个交易日
    如果传入的是交易日：
        1.时间点calculation_completion_time_point之前，则取上个交易日
        2.时间点calculation_completion_time_point之后，则取传入日期

    Parameters
    ----------
    end_date 传入日期

    Returns
    -------
    real_date 实际存在策略信号日期
    """
    real_date = end_date
    if (not FastTdate.is_tdate(end_date)) or (end_date.date() == datetime.utcnow().date() and datetime.now().hour < settings.calculation_completion_time_point):
        real_date = FastTdate.last_tdate(end_date)
    return real_date


def str_of_today() -> str:
    """
    返回当天的字符串格式YYYYMMDD
    :return:
    """
    return datetime.now().strftime("%Y%m%d")


def current_time():
    """
    返回当天的字符串格式HHMMSS
    :return:
    """
    return datetime.now().strftime("%H%M%S")


def datetime2str(d: Union[date, datetime, Iterable[datetime]]) -> Union[str, Iterable[str]]:
    """
    将 datetime 转换为 YYYYMMDD 的格式
    :param d: 可以为单个对象或者可迭代对象
    :return: 单个字符串或者多个字符串
    :raise TypeError
    """
    if isinstance(d, (datetime, date)):
        return datetime.strftime(d, "%Y%m%d")
    elif isinstance(d, Iterable):
        return [datetime2str(item) for item in d]
    else:
        raise TypeError("参数类型必须是 datetime.datetime, 或者由其组成的可迭代对象")


def str2datetime(d: Union[str, Iterable[str]]):
    """
    将 YYYYMMDD 格式的表示日期的字符串转换成对应的 datetime 格式
    :param d: 可以为单个对象或者可迭代对象
    :return: 对应的日期
    :raise TypeError 参数类型错误
    """
    if isinstance(d, str):
        return datetime.strptime(d, "%Y%m%d")
    elif isinstance(d, Iterable):
        return [str2datetime(item) for item in d]
    else:
        raise TypeError("参数类型必须是 str, 或者由其组成的可迭代对象")


def shift_month_datetime(tdate: datetime, months: int) -> datetime:
    """
    获取tdate前n个月开始时间，或后n个月开始时间
    params: tdate type datetime
    params: months type int 正数表示后n个月，负数表示前n个月
    """
    assert 1 <= abs(months) <= 12
    year, month, day = tdate.year, tdate.month, tdate.day
    month += months
    if month > 12:
        year += 1
        month -= 12
    elif month < 1:
        year -= 1
        month += 12
    day = min(calendar.monthrange(year, month)[1], day)
    return datetime(year, month, day)
