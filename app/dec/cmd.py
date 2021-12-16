from functools import wraps

import typer


def typer_log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        typer.echo(f"{func.__name__}{'*'*30} start")
        rsp = func(*args, **kwargs)
        typer.echo(f"{func.__name__}{'*'*30} end")
        return rsp

    return wrapper
