import datetime
from typing import Optional

from stralib import FastTdate


def date2datetime(
    date: Optional[datetime.date] = None, time: str = "min"
) -> datetime.datetime:
    """Date转换为Datetime.

    Parameters
    ----------
    date: 日期
    time: 时间, 可选值为`max` or `min`
        当值为`min`时返回该日期最小的datetime时间, 当值为`max`时返回该日期最大的datetime时间
    """
    if date is None:
        date = datetime.datetime.today()
    time_ = (
        datetime.datetime.min.time() if time == "min" else datetime.datetime.max.time()
    )
    return datetime.datetime.combine(date, time_)


def get_utc_now() -> datetime:
    """获取UTC时间."""
    return datetime.datetime.now(datetime.timezone.utc)


def date2tdate(dt: datetime) -> datetime:
    """date转换为tdate, 若date不是tdate则返回上一个tdate."""
    if FastTdate.is_tdate(dt):
        rv = dt
    else:
        rv = FastTdate.last_tdate(dt)
    return rv


def get_seconds(t: datetime.time) -> int:
    """获取当前时间到指定时间的时间差."""
    now = datetime.datetime.now()
    end = datetime.datetime(now.year, now.month, now.day, t.hour, t.minute, t.second)
    return (end - now).seconds
