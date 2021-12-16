from fastapi.encoders import jsonable_encoder

from app.enums.activity import 活动状态


def test_create_view(fixture_client, fixture_settings, activity_data_in_create, free_user_headers, root_user_headers):
    """创建活动"""
    # 权限不足
    response = fixture_client.post(f"{fixture_settings.url_prefix}/activity", json=jsonable_encoder(activity_data_in_create), headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.post(f"{fixture_settings.url_prefix}/activity", json=jsonable_encoder(activity_data_in_create), headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["name"] == activity_data_in_create["activity"]["name"]


def test_list_view(fixture_client, fixture_settings, activity_data_in_create, root_user_headers):
    """获取活动列表"""
    response = fixture_client.post(f"{fixture_settings.url_prefix}/activity", json=jsonable_encoder(activity_data_in_create), headers=root_user_headers)
    assert response.status_code == 200
    # 查看列表
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/activity/list",
        params={
            "status": 活动状态.online,
            "name": activity_data_in_create["activity"]["name"],
            "start_time": activity_data_in_create["activity"]["start_time"],
            "end_time": activity_data_in_create["activity"]["end_time"],
        },
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["name"] == activity_data_in_create["activity"]["name"]
    assert response.json()[0]["status"] == 活动状态.online


def test_delete_view(fixture_client, fixture_settings, free_user_headers, root_user_headers, fixture_activity):
    """删除活动"""
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/activity/{fixture_activity['_id']}", headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/activity/{fixture_activity['_id']}", headers=root_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    # 已删除
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/activity/{fixture_activity['_id']}", headers=root_user_headers)
    assert response.status_code == 200
    assert "failed" in response.text


def test_put_view(fixture_client, fixture_settings, root_user_headers, fixture_activity):
    """全量更新活动"""
    update_data = fixture_activity.copy()
    update_data["name"] = "test_activity2"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/activity/{fixture_activity['_id']}", json=jsonable_encoder({"activity": update_data}), headers=root_user_headers
    )
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1


def test_patch_view(fixture_client, fixture_settings, root_user_headers, fixture_activity):
    """部分更新活动"""
    update_data = {"activity": {"name": "test_activity3"}}
    response = fixture_client.patch(
        f"{fixture_settings.url_prefix}/activity/{fixture_activity['_id']}", json=jsonable_encoder(update_data), headers=root_user_headers
    )
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1


def test_get_view(fixture_client, fixture_settings, vip_user_headers, fixture_activity):
    """获取活动"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/activity/{fixture_activity['_id']}", headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["name"] == fixture_activity["name"]


def test_create_activity_yield_rank_view(fixture_client, fixture_settings, activity_yield_rank_in_create_data, free_user_headers, root_user_headers):
    """创建活动收益排行"""
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/activity/yield_rank", json=jsonable_encoder(activity_yield_rank_in_create_data), headers=free_user_headers
    )
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/activity/yield_rank", json=jsonable_encoder(activity_yield_rank_in_create_data), headers=root_user_headers
    )
    assert response.status_code == 200
    assert response.json()["profit_rate"] == activity_yield_rank_in_create_data["activity_yield_rank"]["profit_rate"]
    assert response.json()["over_percent"] == activity_yield_rank_in_create_data["activity_yield_rank"]["over_percent"]


def test_activity_yield_ranks_list_view(fixture_client, fixture_settings, activity_yield_rank_in_create_data, root_user_headers):
    """获取活动收益排行列表"""
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/activity/yield_rank", json=jsonable_encoder(activity_yield_rank_in_create_data), headers=root_user_headers
    )
    assert response.status_code == 200
    # 查看列表
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/activity/yield_rank/list",
        params={
            "portfolio": activity_yield_rank_in_create_data["activity_yield_rank"]["portfolio"],
            "activity": activity_yield_rank_in_create_data["activity_yield_rank"]["activity"],
        },
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["activity"] == activity_yield_rank_in_create_data["activity_yield_rank"]["activity"]


def test_activity_yield_rank_delete_view(fixture_client, fixture_settings, activity_yield_rank_in_create_data, free_user_headers, root_user_headers):
    """删除活动收益排行"""
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/activity/yield_rank", json=jsonable_encoder(activity_yield_rank_in_create_data), headers=root_user_headers
    )
    assert response.status_code == 200
    activity_yield_rank_id = response.json()["_id"]
    # 权限不足
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/activity/yield_rank/{activity_yield_rank_id}", headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/activity/yield_rank/{activity_yield_rank_id}", headers=root_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    # 重复删除
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/activity/yield_rank/{activity_yield_rank_id}", headers=root_user_headers)
    assert response.status_code == 200
    assert "failed" in response.text


def test_activity_yield_rank_put_view(fixture_client, fixture_settings, activity_yield_rank_in_create_data, root_user_headers):
    """全量更新活动收益排行"""
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/activity/yield_rank", json=jsonable_encoder(activity_yield_rank_in_create_data), headers=root_user_headers
    )
    assert response.status_code == 200
    activity_yield_rank_id = response.json()["_id"]
    update_data = response.json()
    update_data["rank"] = 2
    # 正例
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/activity/yield_rank/{activity_yield_rank_id}",
        json=jsonable_encoder({"activity_yield_rank": update_data}),
        headers=root_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1


def test_activity_yield_rank_patch_view(fixture_client, fixture_settings, activity_yield_rank_in_create_data, root_user_headers):
    """部分更新活动收益排行"""
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/activity/yield_rank", json=jsonable_encoder(activity_yield_rank_in_create_data), headers=root_user_headers
    )
    assert response.status_code == 200
    activity_yield_rank_id = response.json()["_id"]
    update_data = {"activity_yield_rank": {"rank": 2}}
    # 正例
    response = fixture_client.patch(
        f"{fixture_settings.url_prefix}/activity/yield_rank/{activity_yield_rank_id}", json=jsonable_encoder(update_data), headers=root_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1


def test_activity_yield_rank_get_view(fixture_client, fixture_settings, activity_yield_rank_in_create_data, vip_user_headers, root_user_headers):
    """获取活动收益排行"""
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/activity/yield_rank", json=jsonable_encoder(activity_yield_rank_in_create_data), headers=root_user_headers
    )
    assert response.status_code == 200
    activity_yield_rank_id = response.json()["_id"]
    rank = response.json()["rank"]
    # 正例
    response = fixture_client.get(f"{fixture_settings.url_prefix}/activity/yield_rank/{activity_yield_rank_id}", headers=vip_user_headers,)
    assert response.status_code == 200
    assert response.json()["_id"] == activity_yield_rank_id
    assert response.json()["rank"] == rank
