import asyncio

from pytest import fixture, mark

pytestmark = mark.asyncio


@fixture(autouse=True, scope="module")
def remove_test_log_type(fixture_settings, fixture_db):
    asyncio.get_event_loop().run_until_complete(
        fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ZVT_DATA_LOG_TYPE].delete_many(
            {"name": {"$regex": "^测试"}}
        )
    )


@fixture
def zvt_data_log_type(fixture_settings, fixture_db) -> dict:
    data = {"name": "测试类别"}
    result = asyncio.get_event_loop().run_until_complete(
        fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ZVT_DATA_LOG_TYPE].insert_one(data)
    )
    data["_id"] = result.inserted_id
    yield data
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ZVT_DATA_LOG_TYPE].delete_one({"_id": data["_id"]})


@fixture
def zvt_data_log_dict(zvt_data_log_type) -> dict:
    data = {
        "data_type": zvt_data_log_type["name"],
        "name": "个股资料",
        "data_class": "Stock",
        "desc": "个股和板块为多对多的关系，支持沪深市场，港股，美股",
        "update_time": "每日15:30起",
        "state": "已完成",
    }
    return data


def test_create_zvt_data_log_view(fixture_client, fixture_settings, free_user_headers, zvt_data_log_dict):
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/zvt_data_log/",
        headers=free_user_headers, json=zvt_data_log_dict
    )
    assert response.status_code == 200
    assert response.json()["_id"]


def test_create_zvt_data_log_type_view(fixture_client, fixture_settings, free_user_headers, fixture_db):
    data = {"name": "测试类别"}
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/zvt_data_log/data_type/",
        headers=free_user_headers, json=data
    )
    assert response.status_code == 200
    assert response.json()["_id"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ZVT_DATA_LOG_TYPE].delete_one(
        {"_id": response.json()["_id"]}
    )


def test_get_zvt_data_log_type_list_view(fixture_client, fixture_settings, free_user_headers, zvt_data_log_type):
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/zvt_data_log/data_type/", headers=free_user_headers
    )
    assert response.status_code == 200
    assert zvt_data_log_type["name"] in [type_["name"] for type_ in response.json()]


def test_update_zvt_data_log_type_view(fixture_client, fixture_settings, free_user_headers, zvt_data_log_type):
    data = {"name": "测试测试"}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/zvt_data_log/data_type/{zvt_data_log_type['_id']}", headers=free_user_headers,
        json=data
    )
    assert response.status_code == 200


@fixture
def zvt_data_log_in_db(
    fixture_client, fixture_settings, free_user_headers, zvt_data_log_dict
):
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/zvt_data_log/",
        headers=free_user_headers, json=zvt_data_log_dict
    )
    assert response.status_code == 200
    return response.json()


def test_list_zvt_data_log_view(
    fixture_client, fixture_settings, free_user_headers, zvt_data_log_in_db, zvt_data_log_dict
):
    response = fixture_client.get(f"{fixture_settings.url_prefix}/zvt_data_log/", headers=free_user_headers)
    assert response.status_code == 200
    response1 = fixture_client.get(f"{fixture_settings.url_prefix}/zvt_data_log/?data_type="
                                   f"{zvt_data_log_dict['data_type']}", headers=free_user_headers)
    assert response1.status_code == 200
    assert zvt_data_log_in_db["_id"] in [obj.get("_id") for obj in response1.json()]


def test_get_zvt_data_log_view(
    fixture_client, fixture_settings, free_user_headers, zvt_data_log_in_db
):
    response = fixture_client.get(f"{fixture_settings.url_prefix}/zvt_data_log/{zvt_data_log_in_db['_id']}",
                                  headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["_id"] == zvt_data_log_in_db["_id"]


# def test_update_zvt_data_log_view(
#     fixture_client, fixture_settings, free_user_headers, zvt_data_log_in_db
# ):
#     raw_data = copy(zvt_data_log_in_db)
#     del raw_data["_id"]
#     raw_data["state"] = "未完成"
#     response = fixture_client.put(f"{fixture_settings.url_prefix}/zvt_data_log/{zvt_data_log_in_db['_id']}",
#                                   headers=free_user_headers, json=raw_data)
#     assert response.status_code == 200
#     assert response.json()["modified_count"] == 1


def test_partial_update_zvt_data_log_view(
    fixture_client, fixture_settings, free_user_headers, zvt_data_log_in_db
):
    data = {"state": "未完成"}
    response = fixture_client.put(f"{fixture_settings.url_prefix}/zvt_data_log/{zvt_data_log_in_db['_id']}",
                                    headers=free_user_headers, json=data)
    assert response.status_code == 200
    assert response.json()["modified_count"] == 1


def test_delete_zvt_data_log_view(
    fixture_client, fixture_settings, free_user_headers, zvt_data_log_in_db
):
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/zvt_data_log/{zvt_data_log_in_db['_id']}",
                                     headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["result"] == "success"


def test_delete_zvt_data_log_type_view(
    fixture_client, fixture_settings, free_user_headers, fixture_db
):
    data = {"name": "测试类别"}
    result = asyncio.get_event_loop().run_until_complete(
        fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.ZVT_DATA_LOG_TYPE].insert_one(data)
    )
    data["_id"] = result.inserted_id
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/zvt_data_log/data_type/{data['_id']}",
                                     headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()["result"] == "success"
