def test_get_self_permissions(fixture_client, fixture_settings, root_user_headers, free_user_headers, airflow_user_headers):
    """获取当前用户自己的所有权限"""
    # 免费用户
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions", headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:查看" in response.text
    # 超级用户
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions?exclude_role=false", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json() == {"permissions": {"*": ["*"]}, "role": None}
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions?exclude_role=true", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json() == {"permissions": {"*": ["*"]}, "role": None}
    # 策略管理员
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions", headers=airflow_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:查看" in response.text


def test_query_user_permissions(
    fixture_client, fixture_settings, free_user_data, root_user_data, airflow_user_data, root_user_headers, free_user_headers, airflow_user_headers
):
    """获取某用户的所有权限"""
    # 免费用户
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/{free_user_data['user']['username']}", headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:查看他人" in response.text
    # 超级用户
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/1212121212", headers=root_user_headers)
    assert response.status_code == 400
    assert "无此用户1212121212" in response.text
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/{free_user_data['user']['username']}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["permissions"] is not None
    # 策略管理员
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/{airflow_user_data['user']['username']}", headers=airflow_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:查看他人" in response.text


def test_query_role_permissions(fixture_client, fixture_settings, airflow_user_data, root_user_headers, free_user_headers, airflow_user_headers):
    """获取某角色的权限"""
    # 免费用户查看权限
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/role/免费用户", headers=free_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:查看他人" in response.text
    # 策略管理员
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/{airflow_user_data['user']['username']}", headers=airflow_user_headers)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:查看他人" in response.text
    # 超级用户查看免费用户权限
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/role/免费用户", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "免费用户"
    assert response.json()["permissions"] != {}
    # 超级用户查看没有的角色权限
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/role/没有的角色", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "没有的角色"
    assert response.json()["permissions"] == {}
    # 超级用户查看超级用户权限
    response = fixture_client.get(f"{fixture_settings.url_prefix}/permissions/role/超级用户", headers=root_user_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "超级用户"
    assert response.json()["permissions"] == {"*": ["*"]}


def test_add_and_delete_permission(fixture_client, fixture_settings, free_user_data, root_user_headers, free_user_headers):
    """增加一条权限"""
    # 权限
    permission = {"role": "测试角色", "permissions": {"测试": ["测试"]}}
    roles = {"name": "测试角色"}
    # 新增角色
    response = fixture_client.post(f"{fixture_settings.url_prefix}/roles", headers=root_user_headers, json=roles)
    assert response.status_code == 200
    # 正例
    response = fixture_client.post(f"{fixture_settings.url_prefix}/permissions", headers=root_user_headers, json=permission)
    assert response.status_code == 200
    assert response.json() == permission
    # 异常
    response = fixture_client.post(f"{fixture_settings.url_prefix}/permissions", headers=free_user_headers, json=permission)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:创建他人" in response.text
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/permissions", headers=free_user_headers, json=permission)
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 权限:删除他人" in response.text
    response = fixture_client.post(f"{fixture_settings.url_prefix}/permissions", headers=root_user_headers, json=permission)
    assert response.status_code == 400
    assert f"该角色（{permission['role']}）已有一条权限记录，请删除后再试或者尝试修改记录" in response.text
    permission2 = permission.copy()
    permission2["role"] = "测试角色2"
    response = fixture_client.post(f"{fixture_settings.url_prefix}/permissions", headers=root_user_headers, json=permission2)
    assert response.status_code == 400
    assert f"该角色（{permission2['role']}）不是一条合法的角色，请检查角色列表" in response.text

    # 删除
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/permissions", headers=root_user_headers, json=permission)
    assert response.status_code == 200
    assert "success" in response.text
    # 重复删除
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/permissions", headers=root_user_headers, json=permission)
    assert response.status_code == 400
    assert "权限不存在" in response.text
    # 删除角色
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/roles", headers=root_user_headers, json=roles)
    assert response.status_code == 200
    assert response.json() is True
