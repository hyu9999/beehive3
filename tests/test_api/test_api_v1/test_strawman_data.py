from pytest import mark

from tests.consts.equipment import package_test_data


@mark.skip
def test_get_a_timing_signal_by_sid(fixture_client, fixture_settings, free_user_headers, mocker):
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/timings/03191030pee201?start=2019-01-01&end=2019-03-01", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["list_data"]) > 0
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/timings/03191030pee201?symbol=000300&start=2019-01-01&end=2019-03-01", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["list_data"]) > 0

    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/timings/03191030pee201?symbol=000300&start=2019-01-01&end=2019-03-01&format=dict",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert len(result.json()["dict_data"]) > 0
    # format参数错误情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/timings/03191030pee201?symbol=000300&start=2018-01-01&end=2018-03-01&format=test",
        headers=free_user_headers,
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"] == ["查询失败，原因format参数错误，必须是'list'或'dict'!"]
    # sid不存在的情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/timings/03191030000001?symbol=000300&start=2018-01-01&end=2018-03-01&format=dict",
        headers=free_user_headers,
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"] == ["查询失败，原因03191030000001 table Not Exits  timeseriesstore!"]


@mark.skip
def test_get_a_risk_signal_by_sid(fixture_client, fixture_settings, free_user_headers):
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/risks/04181114sjyj01?start=2019-10-01&end=2019-11-01", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["list_data"]) > 0

    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/risks/04181114sjyj01?start=2019-10-01&end=2019-11-01&format=dict", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["dict_data"]) > 0
    # format参数错误情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/risks/04181114sjyj01?start=2019-10-01&end=2019-11-01&format=test", headers=free_user_headers
    )
    assert result.status_code == 400
    assert result.json()["errors"]["body"] == ["format参数错误，必须是'list'或'dict'!"]
    # sid不存在的情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/risks/04181114000000?start=2019-10-01&end=2019-11-01&format=dict", headers=free_user_headers
    )
    assert result.status_code == 400
    assert result.json()["message"] == "策略信号异常"


@mark.skip
def test_get_a_number_signal_by_sid(fixture_client, fixture_settings, free_user_headers):
    start_date = "2019-03-01"
    end_date = "2019-04-01"
    sid = "04181114st0001"
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/numbers/{sid}?start={start_date}&end={end_date}", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["list_data"]) == 1
    assert result.json()["list_data"][0]["标识符"] == sid
    assert result.json()["list_data"][0]["开始时间"] == start_date
    assert result.json()["list_data"][0]["结束时间"] == end_date
    assert result.json()["list_data"][0]["信号数量"] == 1811

    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/numbers/{sid}?start={start_date}&end={end_date}&format=dict", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["dict_data"]) == 1
    assert end_date in result.json()["dict_data"].keys()
    assert result.json()["dict_data"][end_date][0]["标识符"] == sid
    assert result.json()["dict_data"][end_date][0]["开始时间"] == start_date
    assert result.json()["dict_data"][end_date][0]["结束时间"] == end_date
    assert result.json()["dict_data"][end_date][0]["信号数量"] == 1811
    # format参数错误情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/numbers/{sid}?start={start_date}&end={end_date}&format=test", headers=free_user_headers
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"] == ["查询失败，原因format参数错误，必须是'list'或'dict'!"]
    # sid不存在的情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/risks/04181114000000?start={start_date}&end={end_date}&format=dict", headers=free_user_headers
    )
    assert result.status_code == 400
    assert result.json()["message"] == "策略信号异常"


@mark.skip
def test_get_symbol_number_signal_by_sid(fixture_client, fixture_settings, free_user_headers):
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/symbol_numbers/02180706mav001?symbol=002340&start=2018-01-01&end=2018-03-01",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert len(result.json()["list_data"]) == 1
    assert result.json()["list_data"][0]["标识符"] == "02180706mav001"
    assert result.json()["list_data"][0]["开始时间"] == "2018-01-01"
    assert result.json()["list_data"][0]["结束时间"] == "2018-03-01"
    assert result.json()["list_data"][0]["出现次数"] == 0
    assert result.json()["list_data"][0]["证券代码"] == "002340"

    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/symbol_numbers/02180706mav001?symbol=002340&start=2018-01-01&end=2018-03-01&format=dict",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert len(result.json()["dict_data"]) == 1
    assert "2018-03-01" in result.json()["dict_data"].keys()
    assert result.json()["dict_data"]["2018-03-01"][0]["标识符"] == "02180706mav001"
    assert result.json()["dict_data"]["2018-03-01"][0]["开始时间"] == "2018-01-01"
    assert result.json()["dict_data"]["2018-03-01"][0]["结束时间"] == "2018-03-01"
    assert result.json()["dict_data"]["2018-03-01"][0]["出现次数"] == 0
    assert result.json()["dict_data"]["2018-03-01"][0]["证券代码"] == "002340"
    # format参数错误情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/symbol_numbers/02180706mav001?symbol=002340&start=2018-01-01&end=2018-03-01&format=test",
        headers=free_user_headers,
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"] == ["查询失败，原因format参数错误，必须是'list'或'dict'!"]
    # sid不存在的情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/symbol_numbers/02180706mav555?symbol=002340&start=2018-01-01&end=2018-03-01&format=dict",
        headers=free_user_headers,
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"] == ["查询失败，原因02180706mav555 table Not Exits  timeseriesstore!"]
    # 信号存在某只股票的情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/symbol_numbers/02180706mav001?symbol=600585&start=2018-01-01&end=2018-03-01",
        headers=free_user_headers,
    )
    assert result.json()["list_data"][0]["出现次数"] == 1
    assert result.json()["list_data"][0]["证券代码"] == "600585"


@mark.skip
def test_get_a_screen_signal_by_sid(fixture_client, fixture_settings, free_user_headers):

    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/screens/02180706mav001?start=2018-01-01&end=2019-05-30", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["list_data"]) > 0
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/screens/02180706mav001?start=2018-01-01&end=2019-05-30&format=dict", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["dict_data"]) > 0
    # 测试下返回信号某一天是否有重复的股票
    symbol_list = [x["股票代码"] for x in result.json()["dict_data"]["2019-05-30"]]
    assert len(symbol_list) == len(list(set(symbol_list)))
    # format参数错误情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/screens/02180706mav001?start=2018-01-01&end=2019-05-30&format=test", headers=free_user_headers
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"] == ["查询失败，原因format参数错误，必须是'list'或'dict'!"]
    # 信号为空情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/screens/02180706roe001?start=2009-09-17&end=2009-09-17", headers=free_user_headers
    )
    assert result.status_code == 200
    assert result.json()["list_data"] == []
    # sid不存在的情况
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/signals/screens/02180706roe555?start=2019-09-17&end=2019-09-17", headers=free_user_headers
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"] == ["查询失败，原因02180706roe555 table Not Exits  timeseriesstore!"]


@mark.skip
def test_get_package_signals_numbers_by_sid(fixture_client, fixture_settings, free_user_headers):
    sid = package_test_data["标识符"]
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/package/signals/numbers/{sid}?start=2019-05-30&end=2019-05-30&format=int", headers=free_user_headers
    )
    assert result.status_code == 404
    assert result.json()["errors"]["body"][0] == "查询失败，原因format参数错误，必须是'list'或'dict'!"

    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/package/signals/numbers/{sid}?start=2019-05-30&end=2019-05-30", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["list_data"]) == 2
    assert set(i["标识符"] for i in result.json()["list_data"]) == {"04181114dqzs01", "04181114kthq01"}

    assert set(i["开始时间"] for i in result.json()["list_data"]) == {"2019-05-30"}
    assert set(i["结束时间"] for i in result.json()["list_data"]) == {"2019-05-30"}
    assert [i for i in result.json()["list_data"] if i["标识符"] == "04181114dqzs01"][0]["信号数量"] == 56
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/strawman_data/package/signals/numbers/{sid}?start=2019-05-30&end=2019-05-30&format=dict", headers=free_user_headers
    )
    assert result.status_code == 200
    assert len(result.json()["dict_data"]["2019-05-30"]) == 2
    assert set(i["标识符"] for i in result.json()["dict_data"]["2019-05-30"]) == {"04181114dqzs01", "04181114kthq01"}


@mark.skip
def test_get_package_signals_number_by_sid(fixture_client, fixture_settings, free_user_headers):
    sid = package_test_data["标识符"]
    # wrong
    result = fixture_client.get(f"{fixture_settings.url_prefix}/strawman_data/package/signals/numbers/{sid}/latest?format=int", headers=free_user_headers)
    assert result.status_code == 404
    assert result.json()["errors"]["body"][0] == "查询失败，原因format参数错误，必须是'list'或'dict'!"
    # right
    result = fixture_client.get(f"{fixture_settings.url_prefix}/strawman_data/package/signals/numbers/{sid}/latest", headers=free_user_headers)
    assert result.status_code == 200
    assert len(result.json()["list_data"]) == 2
    assert set(i["标识符"] for i in result.json()["list_data"]) == {"04181114dqzs01", "04181114kthq01"}
    result = fixture_client.get(f"{fixture_settings.url_prefix}/strawman_data/package/signals/numbers/{sid}/latest?format=dict", headers=free_user_headers)
    assert result.status_code == 200
    assert len(result.json()["dict_data"]) > 0
