from typing import List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import UploadFile
from gridfs.errors import NoFile
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.errors import FileUploadError, NoFileError, FileDownloadError, NoRobotError
from app.crud.base import get_gridfs_bucket, get_robots_collection
from app.extentions import logger


async def find(conn: AsyncIOMotorClient, filters: dict):
    """查找文件"""
    fs = get_gridfs_bucket(conn)
    cursor = fs.find(filters, no_cursor_timeout=True)
    ret_data = []
    async for x in cursor:
        ret_data.append(x)
    return ret_data


async def count_documents(conn: AsyncIOMotorClient, filters: dict):
    """获取查询文件数量"""
    queryset = await find(conn, filters)
    return len(queryset)


async def find_one(conn: AsyncIOMotorClient, filters: dict):
    """查找文件"""
    fs = get_gridfs_bucket(conn)
    cursor = fs.find(filters, no_cursor_timeout=True)
    async for grid_data in cursor.limit(-1):
        return grid_data
    return None


async def upload(conn: AsyncIOMotorClient, filename: str, file: UploadFile, metadata: dict = None) -> ObjectId:
    """上传文件"""
    fs = get_gridfs_bucket(conn)
    metadata = metadata or {"contentType": file.content_type}
    try:
        file_id = await fs.upload_from_stream(filename, file.file.read(), metadata=metadata)
    except UploadFile as e:
        logger.error(f"[上传文件失败]{e}")
        raise FileUploadError
    return file_id


async def reupload(conn: AsyncIOMotorClient, filename: dict, file: UploadFile) -> ObjectId:
    """重新上传文件"""
    fs = get_gridfs_bucket(conn)
    old_file = await fs.find_one({"filename": filename})
    if old_file:
        fs.delete(old_file._id)
    file_id = await fs.upload_from_stream(filename, file.file.read())
    return file_id


async def batch_upload(conn: AsyncIOMotorClient, files: List[UploadFile]):
    """批量上传文件"""
    file_id_list = []
    for file in files:
        file_id = await upload(conn, file.filename, file)
        file_id_list.append(file_id)
    return file_id_list


async def download_stream(conn: AsyncIOMotorClient, sid: str):
    """ 下载保存在数据库中的图像文件 """
    fs = get_gridfs_bucket(conn)
    robot_info = await get_robots_collection(conn).find_one({"标识符": sid})
    if robot_info:
        try:
            id = ObjectId(robot_info["头像"])
            file = await fs.open_download_stream(id)
            return file
        except InvalidId:
            logger.error(f"请检查ID是否正确，ID格式错误：{id}")
            raise FileDownloadError
        except NoFile:
            logger.error("没有找到机器人头像文件，请联系管理员。")
            raise NoFileError
    else:
        raise NoRobotError


async def download_by_id(conn: AsyncIOMotorClient, file_id: ObjectId):
    """通过文件id下载文件"""
    fs = get_gridfs_bucket(conn)
    try:
        file = await fs.open_download_stream(file_id)
    except NoFile:
        raise NoFileError
    return file


async def download_by_name(conn: AsyncIOMotorClient, filename: str):
    """通过文件名下载文件"""
    fs = get_gridfs_bucket(conn)
    try:
        file = await fs.open_download_stream_by_name(filename)
    except NoFile:
        raise NoFileError
    return file


async def delete(conn: AsyncIOMotorClient, file_id: ObjectId):
    """删除文件"""
    fs = get_gridfs_bucket(conn)
    await fs.delete(file_id)
