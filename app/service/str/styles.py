import re


def hump2underline(hump_str):
    """
    驼峰形式字符串转成下划线形式
    :param hump_str: 驼峰形式字符串
    :return: 字母全小写的下划线形式字符串
    """
    # 匹配正则，匹配小写字母和大写字母的分界位置
    p = re.compile(r"([a-z]|\d)([A-Z])")
    # 这里第二个参数使用了正则分组的后向引用
    sub = re.sub(p, r"\1_\2", hump_str).lower()
    return sub


def underline2hump(underline_str):
    """
    下划线形式字符串转成驼峰形式
    :param underline_str: 下划线形式字符串
    :return: 驼峰形式字符串
    """
    # 这里re.sub()函数第二个替换参数用到了一个匿名回调函数，回调函数的参数x为一个匹配对象，返回值为一个处理后的字符串
    sub = re.sub(r"(_\w)", lambda x: x.group(1)[1].upper(), underline_str)
    return sub


def to_hump_dict(src: dict):
    res = {}
    for k, v in src.items():
        if isinstance(v, dict):
            res[underline2hump(k)] = to_hump_dict(v)
        elif isinstance(v, list):
            data = []
            for item in v:
                tmp = to_hump_dict(item)
                data.append(tmp)
            res[underline2hump(k)] = data
        else:
            res[underline2hump(k)] = v
    return res


def to_underline_dict(src: dict):
    res = {}
    for k, v in src.items():
        if isinstance(v, dict):
            res[hump2underline(k)] = to_underline_dict(v)
        elif isinstance(v, list):
            data = []
            for item in v:
                tmp = to_underline_dict(item)
                data.append(tmp)
            res[hump2underline(k)] = data
        else:
            res[hump2underline(k)] = v

    return res


def change_styles():
    """驼峰形式字符串转成下划线形式"""

    def make_wrapper(func):
        def wrapper(*args, **kwargs):
            new_args = [to_underline_dict(x) if isinstance(x, dict) else x for x in list(args)[:]]
            new_kwargs = to_underline_dict(kwargs)
            return to_hump_dict(func(*new_args, **new_kwargs))

        return wrapper

    return make_wrapper


def change_input_styles():
    """驼峰形式字符串转成下划线形式"""

    def make_wrapper(func):
        def wrapper(*args, **kwargs):
            new_args = [to_underline_dict(x) if isinstance(x, dict) else x for x in list(args)[:]]
            new_kwargs = to_underline_dict(kwargs)
            return func(*new_args, **new_kwargs)

        return wrapper

    return make_wrapper
