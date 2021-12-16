import asyncio
import os
from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import UploadFile
from pytest import fixture, mark
from stralib import FastTdate

from app.crud.file import delete, upload, find_one
from app.db.mongodb import get_database


@fixture
def fixture_robot_avatar(fixture_client, fixture_settings, root_user_headers):
    db = asyncio.get_event_loop().run_until_complete(get_database())
    data = []
    new_file_list = []
    for i in range(1, 11):
        json_params = {"filename": f"机器人默认头像{i}"}
        file_obj = asyncio.get_event_loop().run_until_complete(find_one(db, json_params))
        if file_obj:
            response = {"filename": json_params["filename"], "file_id": file_obj._id}
        else:
            with open(f"机器人默认头像{i}.png", "wb+") as f:
                files = [
                    ("file", (f"机器人默认头像{i}", f)),
                ]
                response = fixture_client.post(f"{fixture_settings.url_prefix}/common/file/upload", files=files, json=json_params, headers=root_user_headers)
                new_file_list.append(response.json())
            os.remove(f"机器人默认头像{i}.png")
        data.append(response)
    yield data

    for i in new_file_list:
        file_id = i["file_id"]
        asyncio.get_event_loop().run_until_complete(delete(db, ObjectId(file_id)))


@fixture
def fixture_one_pic(fixture_client):
    db = asyncio.get_event_loop().run_until_complete(get_database())
    with open("fixture_one_pic.png", "wb+") as f:
        f.write(b"i am a pic")
        upload_file = UploadFile("测试图片1", file=f, content_type="image/png")
        file_id = asyncio.get_event_loop().run_until_complete(upload(db, "测试图片1", upload_file))
        yield file_id
    os.remove("fixture_one_pic.png")
    asyncio.get_event_loop().run_until_complete(delete(db, file_id))


@fixture
def fixture_public_pic(fixture_client):
    db = asyncio.get_event_loop().run_until_complete(get_database())
    with open("fixture_public_pic.png", "wb+") as f:
        f.write(b"i am a pic")
        upload_file = UploadFile("测试图片1", file=f, content_type="image/png")
        metadata = {"content_type": "image/png", "file_type": "机器人头像"}
        file_id = asyncio.get_event_loop().run_until_complete(upload(db, "测试图片1", upload_file, metadata=metadata))
        yield file_id
    os.remove("fixture_public_pic.png")
    asyncio.get_event_loop().run_until_complete(delete(db, file_id))


@fixture
def fixture_non_public_pic(fixture_client):
    db = asyncio.get_event_loop().run_until_complete(get_database())
    with open("fixture_non_public_pic.png", "wb+") as f:
        f.write(b"i am a pic")
        upload_file = UploadFile("测试图片2", file=f, content_type="image/png")
        metadata = {"content_type": "image/png", "file_type": "装备源代码"}
        file_id = asyncio.get_event_loop().run_until_complete(upload(db, "测试图片2", upload_file, metadata=metadata))
        yield file_id
    os.remove("fixture_non_public_pic.png")
    asyncio.get_event_loop().run_until_complete(delete(db, file_id))


def test_is_tdate(fixture_client, fixture_settings):
    """判断是否是交易日"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date", params={"date": "2019-11-28"})
    assert response.status_code == 200
    assert response.json() == {"status": True}

    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date", params={"date": "2019-11-30"})
    assert response.status_code == 200
    assert response.json() == {"status": False}
    # 参数为空
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date")
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "field required"

    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date", params={"date": "20191130"})
    assert response.status_code == 422
    assert response.json()["errors"]["body"] == ["入参错误，详情为：'19700822'"]
    # 出错之后返回值没有"status"，应该怎么办？
    # assert response.json() == {"status": None}


def test_get_all_tdate_in_given_period(fixture_client, fixture_settings):
    """获取某段时间内的所有交易日"""
    # 正向
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date/list", params={"start": "2019-10-10", "end": "2019-10-18"})
    assert response.status_code == 200
    assert len(response.json()["交易日列表"]) == 6
    # 反向：入参错误
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date/list", params={"start": "2019-10-18", "end": "2019-10-10"})
    assert response.status_code == 422
    assert response.json()["errors"]["body"] == ["入参错误，开始时间大于结束时间"]
    # 日期相同，返回空列表
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date/list", params={"start": "2019-10-18", "end": "2019-10-18"})
    assert response.status_code == 200
    assert len(response.json()["交易日列表"]) == 0
    # 参数错误
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/date/list", params={"start": "2019-10-18 01:00", "end": "2019-10-19 02:01"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "invalid date format"


def test_upload_file(fixture_client, fixture_settings, root_user_headers):
    """保密文件上传"""
    with open("test_pic1.png", "wb+") as f:
        response = fixture_client.post(f"{fixture_settings.url_prefix}/common/file/upload", files={"file": f}, headers=root_user_headers)
        assert response.status_code == 200
        assert "file_id" in response.json().keys()
        file_id = ObjectId(response.json()["file_id"])
        response = fixture_client.post(f"{fixture_settings.url_prefix}/common/file/upload", files={"file": f}, headers=root_user_headers)
        assert response.status_code == 200
        assert "file_id" in response.json().keys()
    db = asyncio.get_event_loop().run_until_complete(get_database())
    asyncio.get_event_loop().run_until_complete(delete(db, file_id))
    os.remove("test_pic1.png")


def test_upload_public_file(fixture_client, fixture_settings, root_user_headers):
    """公共文件上传"""
    with open("test_pic1.png", "wb+") as f:
        response = fixture_client.post(f"{fixture_settings.url_prefix}/common/file/upload/public", files={"file": f}, headers=root_user_headers)
        assert response.status_code == 200
        assert "file_id" in response.json().keys()
        file_id = ObjectId(response.json()["file_id"])
        response = fixture_client.post(f"{fixture_settings.url_prefix}/common/file/upload/public", files={"file": f}, headers=root_user_headers)
        assert response.status_code == 200
        assert "file_id" in response.json().keys()
    db = asyncio.get_event_loop().run_until_complete(get_database())
    asyncio.get_event_loop().run_until_complete(delete(db, file_id))
    os.remove("test_pic1.png")


def test_reupload_file(fixture_client, fixture_settings, root_user_headers):
    """文件重新上传"""
    with open("test_pic1.png", "wb+") as f:
        files = {"file": f}
        response = fixture_client.post(f"{fixture_settings.url_prefix}/common/file/reupload", files=files, headers=root_user_headers)
        assert response.status_code == 200
        response = fixture_client.post(f"{fixture_settings.url_prefix}/common/file/reupload", files=files, headers=root_user_headers)
        assert response.status_code == 200
        assert "file_id" in response.json().keys()
        file_id = ObjectId(response.json()["file_id"])
    os.remove("test_pic1.png")
    db = asyncio.get_event_loop().run_until_complete(get_database())
    asyncio.get_event_loop().run_until_complete(delete(db, file_id))


def test_download_file(fixture_client, fixture_settings, root_user_headers, fixture_one_pic):
    """文件下载"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/file/download/{fixture_one_pic}", headers=root_user_headers)
    assert response.status_code == 200


def test_download_file_by_name(fixture_client, fixture_settings, root_user_headers, fixture_one_pic):
    """通过文件名下载文件"""
    params = {"filename": "测试图片1"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/file/download", params=params, headers=root_user_headers)
    assert response.status_code == 200


def test_airflow_download_file_by_name(fixture_client, fixture_settings, free_user_headers, airflow_user_headers, fixture_one_pic):
    """限定仅airflow权限用户通过文件名下载文件"""
    params = {"filename": "测试图片1"}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/airflow/download", params=params, headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/airflow/download", params=params, headers=airflow_user_headers)
    assert response.status_code == 200


def test_download_public_file(fixture_client, fixture_settings, root_user_headers, fixture_public_pic, fixture_non_public_pic):
    """公共文件下载"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/file/download/{fixture_non_public_pic}/public", headers=root_user_headers)
    assert response.status_code == 403
    assert response.json() == {"errors": {"body": ["无权访问的内容"]}}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/file/download/{fixture_public_pic}/public", headers=root_user_headers)
    assert response.status_code == 200


@mark.skip
def test_download_random_avatar(fixture_client, fixture_settings, root_user_headers, fixture_robot_avatar):
    """获取机器人随机头像"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/file/avatar/robot", headers=root_user_headers)
    assert response.status_code == 200
    assert "avatar" in response.json().keys()
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/common/file/avatar/robot?avatar={fixture_robot_avatar[0]['file_id']}", headers=root_user_headers
    )
    assert response.status_code == 200
    assert "avatar" in response.json().keys()
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/file/avatar/robot?avatar={ObjectId()}", headers=root_user_headers)
    assert response.status_code == 400
    assert "获取机器人默认头像失败" in response.text


def test_batch_upload_file(fixture_client, fixture_settings, free_user_headers):
    """文件批量上传"""
    # 参数错误
    with open("test_pic1.png", "wb+") as f1:
        files = {"file": ("test_pic1", f1, "application/octet-stream")}
        response = fixture_client.post(f"{fixture_settings.url_prefix}/common/files/upload", files=files, headers=free_user_headers)
        assert response.status_code == 422
        assert response.json()["detail"] == [{"loc": ["body", "files"], "msg": "field required", "type": "value_error.missing"}]
    # 正向
    with open("test_pic1.png", "wb+") as f1:
        with open("test_pic2.png", "wb+") as f2:
            files = [
                ("files", ("test_pic1", f1)),
                ("files", ("test_pic2", f2)),
            ]
            response = fixture_client.post(f"{fixture_settings.url_prefix}/common/files/upload", files=files, headers=free_user_headers)
            assert response.status_code == 200
            file_id = response.json()
            assert len(response.json()) == len(files)
            # 重复上传
            response = fixture_client.post(f"{fixture_settings.url_prefix}/common/files/upload", files=files, headers=free_user_headers)
            assert response.status_code == 400
            assert response.json() == {"errors": {"body": ["[上传文件失败] 文件名重复"]}}
    os.remove("test_pic1.png")
    os.remove("test_pic2.png")
    db = asyncio.get_event_loop().run_until_complete(get_database())
    asyncio.get_event_loop().run_until_complete(delete(db, ObjectId(file_id[0])))
    asyncio.get_event_loop().run_until_complete(delete(db, ObjectId(file_id[-1])))


def test_real_trade_date(fixture_client, fixture_settings, free_user_headers):
    """获取真正的交易日"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/real_tdate?date=2019-12-31", headers=free_user_headers)
    assert response.json()["tdate"] == "2019-12-31"
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/real_tdate?date=3019-12-31", headers=free_user_headers)
    assert response.status_code == 400
    assert response.json() == {"errors": {"body": ["获取交易日错误：'30191231'"]}}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/real_tdate?date=2020-01-01", headers=free_user_headers)
    assert response.json()["tdate"] == "2019-12-31"
    current_utc_dt = datetime.utcnow()
    current_dt = current_utc_dt + timedelta(hours=8)
    response = fixture_client.get(f"{fixture_settings.url_prefix}/common/trade/real_tdate?date={current_utc_dt.date()}", headers=free_user_headers)
    if current_dt.hour >= fixture_settings.calculation_completion_time_point:
        assert response.json()["tdate"] == current_utc_dt.date().isoformat()
    else:
        assert response.json()["tdate"].replace("-", "") == FastTdate.last_tdate(current_dt.date().strftime("%Y%m%d"))
