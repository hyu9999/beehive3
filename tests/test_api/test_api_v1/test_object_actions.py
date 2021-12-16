def test_get_all_object_and_actions(fixture_client, fixture_settings, root_user_headers):
    """获取所有对象和操作"""
    response = fixture_client.get(f"{fixture_settings.url_prefix}/object_actions", headers=root_user_headers)
    assert response.status_code == 200
    assert "name" in response.json()[0]
    assert "url_prefix" in response.json()[0]
