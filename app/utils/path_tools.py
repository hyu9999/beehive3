import os


def get_file_path(folder_path, filter_name=None):
    """获取符合条件的文件路径"""
    data = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if filter_name:
                if file == filter_name:
                    data.append(os.path.join(root, file))
            else:
                data.append(os.path.join(root, file))
    return data
