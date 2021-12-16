def test_get_roles(fixture_client, fixture_settings, root_user_headers, free_user_headers, airflow_user_headers):
    """获取所有角色"""
    # response = fixture_client.get(f"{fixture_settings.url_prefix}/roles", headers=free_user_headers)
    # assert response.status_code == 400
    # assert "用户权限不足, 需要的权限: 角色:查看" in response.text
    # 策略管理员
    response = fixture_client.get(f"{fixture_settings.url_prefix}/roles", headers=airflow_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 角色:查看" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/roles", headers=root_user_headers)
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_is_valid(fixture_client, fixture_settings, root_user_headers, free_user_headers, airflow_user_headers):
    """角色是否存在"""
    # response = fixture_client.get(f"{fixture_settings.url_prefix}/roles/测试角色", headers=free_user_headers)
    # assert response.status_code == 400
    # assert "用户权限不足, 需要的权限: 角色:查看" in response.text
    # 策略管理员
    response = fixture_client.get(f"{fixture_settings.url_prefix}/roles/测试角色", headers=airflow_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 角色:查看" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/roles/测试角色", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json() is False
    response = fixture_client.get(f"{fixture_settings.url_prefix}/roles/免费用户", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json() is True
    response = fixture_client.get(f"{fixture_settings.url_prefix}/roles/策略管理员", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json() is True


def test_add_and_delete_role(fixture_client, fixture_settings, root_user_headers, free_user_headers, airflow_user_headers):
    """创建角色/删除角色"""
    roles = {"name": "测试角色"}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/roles", headers=free_user_headers, json=roles)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 角色:创建" in response.text

    # 策略管理员
    response = fixture_client.post(f"{fixture_settings.url_prefix}/roles", headers=airflow_user_headers, json=roles)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 角色:创建" in response.text

    response = fixture_client.post(f"{fixture_settings.url_prefix}/roles", headers=root_user_headers, json=roles)
    assert response.status_code == 200

    assert response.json()["name"] == roles["name"]

    # 重复写入
    response = fixture_client.post(f"{fixture_settings.url_prefix}/roles", headers=root_user_headers, json=roles)
    assert response.status_code == 400
    assert "数据库错误" in response.text
    # 删除
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/roles", headers=root_user_headers, json=roles)
    assert response.status_code == 200
    assert response.json() is True
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/roles", headers=root_user_headers, json=roles)
    assert response.status_code == 200
    assert response.json() is False
