from app.enums.tag import TagType


def test_get_tags(fixture_client, fixture_settings, tag_in_db_data, free_user_headers):
    """查看标签列表"""
    # 装备
    response = fixture_client.get(f"{fixture_settings.url_prefix}/tag", params={"分类": tag_in_db_data[0]["category"]}, headers=free_user_headers)
    assert response.status_code == 200
    equipment_tag_result_list = []
    for x in response.json():
        if x not in equipment_tag_result_list:
            equipment_tag_result_list.append(x)
    assert len(response.json()) == len(equipment_tag_result_list)  # 校验去重功能是否有效
    assert [x for x in response.json() if x["category"] != tag_in_db_data[0]["category"]] == []
    # 机器人
    response = fixture_client.get(f"{fixture_settings.url_prefix}/tag", params={"分类": tag_in_db_data[1]["category"]}, headers=free_user_headers)
    assert response.status_code == 200
    robot_tag_result_list = []
    for x in response.json():
        if x not in robot_tag_result_list:
            robot_tag_result_list.append(x)
    assert len(response.json()) == len(robot_tag_result_list)  # 校验去重功能是否有效
    assert [x for x in response.json() if x["category"] != tag_in_db_data[1]["category"]] == []


def test_create_view(fixture_client, fixture_settings, tag_in_create_data, vip_user_headers, free_user_headers):
    """创建标签"""
    tag_list = tag_in_create_data
    category = TagType.装备
    # 权限不足
    response = fixture_client.post(f"{fixture_settings.url_prefix}/tag", params={"tags": tag_list, "category": category}, headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.post(f"{fixture_settings.url_prefix}/tag", params={"tags": tag_list, "category": category}, headers=vip_user_headers)
    assert response.status_code == 200


def test_delete_view(fixture_client, fixture_settings, tag_in_db_data, free_user_headers, vip_user_headers):
    """删除标签"""
    tag_id = tag_in_db_data[0]["_id"]
    # 权限不足
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/tag/{tag_id}", headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/tag/{tag_id}", headers=vip_user_headers)
    assert response.status_code == 200
    assert "success" in response.text
    # 重复删除
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/tag/{tag_id}", headers=vip_user_headers)
    assert response.status_code == 200
    assert "failed" in response.text


def test_put_view(fixture_client, fixture_settings, tag_in_db_data, free_user_headers, vip_user_headers):
    """全量更新标签"""
    update_tag_data = tag_in_db_data[0]
    update_tag_data["name"] = "test_put"
    tag_id = update_tag_data.pop("_id")
    # 权限不足
    response = fixture_client.put(f"{fixture_settings.url_prefix}/tag/{tag_id}", json={"tag": update_tag_data}, headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.put(f"{fixture_settings.url_prefix}/tag/{tag_id}", json={"tag": update_tag_data}, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1


def test_patch_view(fixture_client, fixture_settings, tag_in_db_data, free_user_headers, vip_user_headers):
    """部分更新标签"""
    update_tag_data = {"tag": {"name": "test_put"}}
    tag_id = tag_in_db_data[0].pop("_id")
    # 权限不足
    response = fixture_client.patch(f"{fixture_settings.url_prefix}/tag/{tag_id}", json=update_tag_data, headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足" in response.text
    # 正例
    response = fixture_client.patch(f"{fixture_settings.url_prefix}/tag/{tag_id}", json=update_tag_data, headers=vip_user_headers)
    assert response.status_code == 200
    assert response.json()["matched_count"] == response.json()["modified_count"] == 1
