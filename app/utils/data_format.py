def name_mapping(service_mapping: dict, *items, reverse=False):
    """
    将服务层的模型转换为接口层的模型, 根据 service_mapping
    Parameters
    ----------
    service_mapping 键为接口层的字段名, 值为服务层的字段名
    items   将要转换的多个字典对象
    reverse 转换的方向, True 为正向, False 为反向

    Returns
    -------
    在原字典上修改，返回更改后的字典
    """
    for item in list(items):
        for key, value in service_mapping.items():
            key, value = (value, key) if reverse else (key, value)
            if isinstance(item, dict):
                item[key] = item.pop(value)

    if len(items) == 1:
        return items[0]

    return items
