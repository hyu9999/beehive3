import asyncio
from copy import deepcopy
from datetime import date, datetime

from fastapi.encoders import jsonable_encoder
from stralib import FastTdate

from app.crud.base import get_equipment_collection
from app.db.mongodb import get_database
from app.enums.equipment import 装备状态更新操作类型Enum
from tests.consts.backtest import (
    test_screen_backtest_assess,
    test_screen_backtest_indicator,
    test_screen_backtest_signal,
    test_screen_real_signal,
    test_timing_backtest_assess,
    test_timing_backtest_indicator,
    test_timing_backtest_signal,
    test_timing_real_signal,
)
from tests.consts.equipment import 大类资产配置实盘指标数据
from tests.mocks.db_base import MockConfigCollection
from tests.mocks.equipment import MockEquipmentCollection, mock_nothing
from tests.mocks.signal import mock_get_strategy_signal
from tests.mocks.topic import MockDisc, mock_create_thread


def test_get_equipment_by_sid(fixture_client, fixture_settings, free_user_headers, fixture_create_equipments):
    # 正向测试
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[0]['标识符']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["名称"] == fixture_create_equipments[0]["名称"]
    # 异常：sid不符合规则
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/1000010000001",
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error.str.regex"
    # 异常：未找到sid
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/04000010000001",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["message"] == "没有找到装备sid=04000010000001"


def test_query_equipment_list(fixture_client, fixture_settings, free_user_headers, fixture_create_equipments):
    名称 = fixture_create_equipments[0]["名称"]
    标识符 = fixture_create_equipments[0]["标识符"]
    标识符列表 = [equipment["标识符"] for equipment in fixture_create_equipments]
    状态 = fixture_create_equipments[0]["状态"]
    上线时间 = fixture_create_equipments[0]["上线时间"]
    作者 = fixture_create_equipments[0]["作者"]

    response = fixture_client.get(f"{fixture_settings.url_prefix}/equipment?名称={名称}", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == 标识符

    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?名称={名称}&标识符={标识符}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == 标识符

    response = fixture_client.get(f"{fixture_settings.url_prefix}/equipment?标识符={标识符}", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json()[0]["标识符"] == 标识符

    # 测试标识符列表
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?标识符={标识符列表[0]}&标识符={标识符列表[1]}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert [equipment["标识符"] for equipment in response.json()] == 标识符列表[:2]

    修改后标识符 = "错误的标识符"
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?标识符={修改后标识符}",
        headers=free_user_headers,
    )
    # 校验标识符格式，如果不是"^(01|02|03|04|05|06|07|11)[\\d]{6}[\\w]{4}[\\d]{2}$"，则返回422
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error.str.regex"
    # 测试不存在的名称
    response = fixture_client.get(f"{fixture_settings.url_prefix}/equipment?名称=错误的名称", headers=free_user_headers)
    assert response.status_code == 200
    assert response.json() == []

    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?limit=1000&状态={状态}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    online_equipment_count = len(response.json())
    for skip in range(0, online_equipment_count, 20):
        response = fixture_client.get(
            f"{fixture_settings.url_prefix}/equipment?skip={skip}&状态={状态}",
            headers=free_user_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) in {20, online_equipment_count % 20}

    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?状态={状态}&limit=1000",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # 分类查询，需要输入编码，否则报422
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?分类=选股&上线时间={上线时间}&作者={作者}&limit=1000",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?分类=选股&limit=1000",
        headers=free_user_headers,
    )
    assert response.status_code == 200

    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?分类=选股&作者={作者}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == len([x for x in response.json() if x["分类"] == "选股" and x["作者"]["username"] == 作者])
    # 错误状态
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?分类=aa&作者={作者}",
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.enum"
    # 排序
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?排序=累计产生信号数=-1&作者={作者}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    sort_result_list = [equipment["累计产生信号数"] for equipment in response.json()]
    assert sort_result_list == sorted(sort_result_list, reverse=True)
    # 异常排序
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?排序=产生信号数&作者={作者}",
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["errors"]["body"][0] == "查询装备排序参数错误，请输入规定的排序方式。详细错误：list index out of range"
    # 信号传入方式
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?信号传入方式=源代码传入&作者={作者}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len([x for x in response.json() if x["信号传入方式"] == "源代码传入" and x["作者"]["username"] == 作者]) == len(response.json())
    # 可见模式
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?可见模式=完全公开&作者={作者}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len([x for x in response.json() if x["可见模式"] == "完全公开" and x["作者"]["username"] == 作者]) == len(response.json())
    # 评级
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?评级=A&作者={作者}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len([x for x in response.json() if x["评级"] == "A" and x["作者"]["username"] == 作者]) == len(response.json())
    # limit skip
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?作者={作者}",
        params={"limit": 2, "skip": 1},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len([x for x in response.json() if x["作者"]["username"] == 作者]) == len(response.json()) == 2
    # 模糊查询
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?search_name={作者}",
        params={"limit": 2, "skip": 1},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len([x for x in response.json() if x["名称"] == 作者 or 作者 in x["标签"]]) == len(response.json()) == 0
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?search_name={'test'}&模糊查询={'名称'}",
        params={"limit": 2, "skip": 1},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len([x for x in response.json() if "test" in x["名称"]]) == len(response.json())
    # 分页
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?is_paging=true&最近使用时间_开始=2019-01-01 00:00:00&最近使用时间_结束={上线时间}",
        params={"limit": 2, "skip": 1},
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["数据"]) == 2
    下线时间 = datetime(2020, 7, 1)
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment?下线时间={下线时间}",
        params={"limit": 2, "skip": 1},
        headers=free_user_headers,
    )
    assert response.status_code == 200


def test_query_my_equipment_list(fixture_client, fixture_settings, free_user_headers, fixture_create_equipments):
    # 分类
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/my/list?分类=选股",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == len([x for x in response.json() if x["分类"] == "选股"])
    # 错误分类
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/my/list?分类=xx",
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.enum"
    # 排序
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/my/list?分类=选股&排序=累计产生信号数",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == sorted(response.json(), key=lambda x: x["累计产生信号数"], reverse=True)
    # 异常排序
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/my/list?分类=选股&排序=产生信号数",
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["errors"]["body"][0] == "错误的排序类型"


def test_create_equipment(
    fixture_client,
    fixture_settings,
    free_user_headers,
    vip_user_headers,
    fixture_equipment_in_create_list,
    mocker,
):
    """创建装备"""
    mocker.patch("app.settings.discuzq", MockDisc())
    mocker.patch("app.crud.equipment.create_thread", mock_create_thread)
    # 异常，权限不足
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=fixture_equipment_in_create_list[0],
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert "用户权限不足, 需要的权限: 装备:创建" in response.text
    tmp_data = deepcopy(fixture_equipment_in_create_list[0])
    tmp_data["源代码"] = None
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=tmp_data,
        headers=vip_user_headers,
    )
    assert response.status_code == 422
    assert "源代码字段必须传入！" in response.json()["errors"]["body"][0]
    # 正例
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=fixture_equipment_in_create_list[0],
        headers=vip_user_headers,
    )
    assert response.status_code == 201
    assert response.reason == "Created"
    assert response.json()["状态"] == "审核中"
    # 接口传入
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=fixture_equipment_in_create_list[1],
        headers=vip_user_headers,
    )
    assert response.status_code == 201
    assert response.reason == "Created"
    assert response.json()["状态"] == "未审核"
    # 创建包
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=fixture_equipment_in_create_list[-1]["包"],
        headers=vip_user_headers,
    )
    assert response.status_code == 201
    assert response.reason == "Created"
    # 重复创建抛错
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=fixture_equipment_in_create_list[0],
        headers=vip_user_headers,
    )
    assert response.status_code == 400
    assert response.reason == "Bad Request"
    assert (
        f"创建装备失败，装备名称'{fixture_equipment_in_create_list[0]['名称']}或标识符{fixture_equipment_in_create_list[0].get('标识符')}''已存在！"
        in response.json()["errors"]["body"][0]
    )
    # 创建数量限制
    mocker.patch("app.service.equipment.settings.num_limit", {"VIP用户": {"equipment": 1}})
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=fixture_equipment_in_create_list[0],
        headers=vip_user_headers,
    )
    assert response.status_code == 400
    assert "创建装备数达到上限，最多只能创建1个" in response.text


def test_update_equipment(
    fixture_client,
    fixture_settings,
    free_user_headers,
    vip_user_headers,
    fixture_create_equipments,
):
    """更新装备"""
    update_dict = {"装备": {"名称": "test_选股装备2"}}
    # 权限不足
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[2]['标识符']}",
        json=jsonable_encoder(update_dict),
        headers=vip_user_headers,
    )
    assert response.status_code == 403
    assert f"您没有修改该装备（{fixture_create_equipments[2]['标识符']}）的权限" in response.text
    # 已下线状态更新
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[2]['标识符']}",
        json=jsonable_encoder(update_dict),
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["名称"] == "test_选股装备2"
    # sid传入错误
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/aaaa",
        json=jsonable_encoder(update_dict),
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error.str.regex"


def test_update_equipment_operational(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_create_equipments,
    mocker,
):
    """更新装备运行数据"""
    mocker.patch("app.service.equipment.get_strategy_signal", mock_get_strategy_signal)
    # 非上线和下线状态的装备不允许修改运行数据
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[0]['标识符']}/operational",
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["errors"]["body"][0] == "[更新装备运行数据失败]"
    # 已上线状态更新（装备）
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[1]['标识符']}/operational",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    # 已上线状态更新（风控包）
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/11000000test01/operational",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    # sid传入错误
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/aaaa/operational",
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error.str.regex"
    # 厂商环境
    mocker.patch(
        "app.crud.equipment.settings.manufacturer_switch",
        return_value=True,
    )
    装备 = {"装备": {"订阅人数": 10}}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/11000000test01/operational",
        json=装备,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}


def test_update_equipment_status(
    fixture_client,
    fixture_settings,
    free_user_headers,
    vip_user_headers,
    fixture_create_equipments,
    fixture_equipment_in_create_list,
    mocker,
):
    """更新装备状态"""
    mocker.patch("app.settings.discuzq", MockDisc())
    mocker.patch("app.crud.equipment.create_thread", mock_create_thread)
    # 已上线状态不允许切换
    equipment_state_in_update = {"操作类型": 装备状态更新操作类型Enum.装备上线}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[1]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["message"] == "原状态不允许切换"
    # 装备上线
    equipment_state_in_update = {"操作类型": 装备状态更新操作类型Enum.装备上线}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[1]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["message"] == "原状态不允许切换"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[3]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    # 装备下线
    equipment_state_in_update = {"操作类型": 装备状态更新操作类型Enum.装备下线}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[0]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["message"] == "原状态不允许切换"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[1]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    # 装备删除
    equipment_state_in_update = {"操作类型": 装备状态更新操作类型Enum.装备删除}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[0]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["message"] == "装备状态错误"
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[1]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    # 未查询到该动作
    equipment_state_in_update = {"操作类型": "xxx"}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[0]['标识符']}/action",
        json=equipment_state_in_update,
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert "value is not a valid enumeration member" in response.json()["detail"][0]["msg"]
    # 包
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/new",
        json=fixture_equipment_in_create_list[-1]["包"],
        headers=vip_user_headers,
    )
    assert response.status_code == 201
    assert "标识符" in response.json()
    包标识符 = response.json()["标识符"]
    # 包下线
    equipment_state_in_update = {"操作类型": 装备状态更新操作类型Enum.装备下线}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{包标识符}/action",
        json=equipment_state_in_update,
        headers=vip_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}
    # 包删除
    equipment_state_in_update = {"操作类型": 装备状态更新操作类型Enum.装备删除}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{包标识符}/action",
        json=equipment_state_in_update,
        headers=vip_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}


def test_delete_a_equipment(fixture_client, fixture_settings, root_user_headers, fixture_create_equipments):
    """删除装备"""
    标识符 = fixture_create_equipments[0]["标识符"]
    # 正向
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/equipment/{标识符}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.text == "1"
    # 重复删除
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/equipment/{标识符}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.text == "0"
    # 不存在的标识符
    标识符 = "02112345678111"
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/equipment/{标识符}", headers=root_user_headers)
    assert response.status_code == 200
    assert response.text == "0"
    # 标识符不符合规则
    sid = "adasd1"
    response = fixture_client.delete(f"{fixture_settings.url_prefix}/equipment/{sid}", headers=root_user_headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error.str.regex"


def test_candlestick_chart(fixture_client, fixture_settings, free_user_headers):
    """指数k线图"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/candlestick/market?symbol=399001&start=2019-10-01&end=2019-11-20",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    rsp_dict = response.json()
    assert "时间戳" in rsp_dict[0].keys()
    assert "2019-11-20" in rsp_dict[-1].values()

    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/candlestick/market?symbol=000001&start=2019-10-01&end=2019-11-20",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    rsp_dict = response.json()
    assert "时间戳" in rsp_dict[0].keys()
    # 开始时间等于结束时间
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/candlestick/market?symbol=000001&start=2019-11-20&end=2019-11-20",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "时间戳" in response.json()[0].keys()


def test_get_equipment_backtest_indicator(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_insert_equipment_backtest_real_data,
):
    """获取某装备的回测指标"""
    # 择时
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_timing_backtest_indicator['标识符']}/backtest_indicator?symbol=000300",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()[0]["标的指数"] == "000300"
    # 选股
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_screen_backtest_indicator['标识符']}/backtest_indicator",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    # 风控
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/04180629wr0099/backtest_indicator",
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert result.json()["errors"]["body"][0] == "查询装备(04180629wr0099)回测指标发生错误，错误信息: 暂不支持的sid类型(04180629wr0099)"
    # 查询不存在信息的sid
    标识符 = "03180629wr0199"
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{标识符}/backtest_indicator",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == []


def test_get_equipment_signal(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_insert_equipment_backtest_real_data,
):
    """获取某装备的回测信号"""
    start, end = date(2018, 1, 1), date(2019, 3, 1)
    # 择时
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_timing_backtest_signal['标识符']}/backtest_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()[0]["标的指数"] == "000300"
    # 选股
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_screen_backtest_signal['标识符']}/backtest_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()[0]["累计收益率"] == 1.9496
    # 风控
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/04180629wr0099/backtest_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert result.json()["errors"]["body"][0] == "查询装备(04180629wr0099)回测信号发生错误，错误信息: 暂不支持的sid类型(04180629wr0099)"
    # 查询不存在信息的sid
    标识符 = "03180629wr0199"
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{标识符}/backtest_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == []
    # 参数错误
    start, end = datetime(2018, 1, 1), datetime(2018, 3, 1)
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_screen_backtest_signal['标识符']}/backtest_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["loc"] == ["query", "start"]


def test_get_equipment_backtest_assess(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_insert_equipment_backtest_real_data,
):
    """获取某装备的回测评级"""
    market_index = "000300"
    # 择时
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_timing_backtest_assess['标识符']}/backtest_assess?symbol={market_index}",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()[0]["标的指数"] == market_index
    # 选股
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_screen_backtest_assess[0]['标识符']}/backtest_assess",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()[0]["评级"] == "A"
    # 风控
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/04180629wr0099/backtest_assess",
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert result.json()["errors"]["body"][0] == "查询装备(04180629wr0099)回测评级发生错误，错误信息: 暂不支持的sid类型(04180629wr0099)"
    # 查询不存在信息的sid
    标识符 = "03180629wr0199"
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{标识符}/backtest_assess?",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == []


def test_get_equipment_real_signal(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_insert_equipment_backtest_real_data,
):
    """获取某装备的实盘信号"""
    start, end = date(2017, 1, 1), date(2019, 12, 13)
    # 择时
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_timing_real_signal['标识符']}/real_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()[0]["标的指数"] == "399006"
    # 选股
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_screen_real_signal['标识符']}/real_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()[0]["累计收益率"] == 0.2354
    # 风控
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/04180629wr0099/real_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert result.json()["errors"]["body"][0] == "暂不支持的sid类型(04180629wr0099)"
    # 查询不存在信息的sid
    标识符 = "03180629wr0199"
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{标识符}/real_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == []
    # 参数错误
    start, end = datetime(2018, 1, 1), datetime(2018, 3, 1)
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{test_screen_real_signal['标识符']}/real_signal?start={start}&end={end}",
        headers=free_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["loc"] == ["query", "start"]


def test_get_equipment_backtest_details(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_insert_equipment_backtest_real_data,
):
    """获取选股装备的回测评级详情"""
    # 正向
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/backtest/details/{test_screen_backtest_assess[0]['标识符']}?数据集=整体评级",
        headers=free_user_headers,
    )
    assert result.status_code == 200
    assert result.json()["选股装备回测评级"]["评级"] == "A"
    assert result.json()["选股装备回测指标"]["Alpha"] == 0.148
    assert result.json()["选股装备回测信号"]["累计收益率"] == 1.9496
    # 获取不到选股装备回测评级
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/backtest/details/{test_screen_backtest_assess[0]['标识符']}?数据集=训练集评级",
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert result.json()["message"] == f"查询装备({test_screen_backtest_assess[0]['标识符']})回测评级发生错误"
    # 选股装备回测指标/信号为None
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/backtest/details/{test_screen_backtest_assess[1]['标识符']}",
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert result.json()["message"] == f"查询装备({test_screen_backtest_assess[1]['标识符']})回测信息发生错误"
    # 参数错误
    result = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/backtest/details/{test_screen_backtest_assess[0]['标识符']}?数据集=xxx",
        headers=free_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "type_error.enum"


def test_create_timings_backtest_signal(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_insert_equipment_backtest_real_data,
):
    """创建择时装备的回测信号数据"""
    # 正向
    test_timing_backtest_signal["交易日期"] = datetime(2018, 1, 2)
    test_timing_backtest_signal.pop("_id")
    data = {"装备回测信号数据": [test_timing_backtest_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    # 不允许重复写入
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json()["message"] == "[03000000test01]数据重复写入."
    # 插入空数据
    data = {"装备回测信号数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备回测信号失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_timing_backtest_signal.pop("收益率")
    data = {"装备回测信号数据": [test_timing_backtest_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_signal",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_create_screens_backtest_signal(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_insert_equipment_backtest_real_data,
    mocker,
):
    """创建选股装备的回测信号数据"""
    mocker.patch("app.crud.equipment.策略数据完整性检验", mock_nothing)
    # 正向
    test_screen_backtest_signal["交易日期"] = datetime(2019, 1, 1)
    test_screen_backtest_signal.pop("_id")
    data = {"装备回测信号数据": [test_screen_backtest_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == {"result": "success"}
    # 插入空数据
    data = {"装备回测信号数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备回测信号失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_screen_backtest_signal.pop("收益率")
    data = {"装备回测信号数据": [test_screen_backtest_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_signal",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_create_timings_backtest_indicator(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_insert_equipment_backtest_real_data,
    mocker,
):
    """创建择时装备的回测指标数据"""
    mocker.patch("app.crud.equipment.策略数据完整性检验", mock_nothing)

    # 正向
    test_timing_backtest_indicator["收益率"] = 1.23
    test_timing_backtest_indicator.pop("_id")
    data = {"装备回测指标数据": [test_timing_backtest_indicator]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == {"result": "success"}
    # 插入空数据
    data = {"装备回测指标数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备回测指标失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_timing_backtest_indicator.pop("收益率")
    data = {"装备回测指标数据": [test_timing_backtest_indicator]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_indicator",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_create_screens_backtest_indicator(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_insert_equipment_backtest_real_data,
    mocker,
):
    """创建选股装备的回测指标数据"""
    mocker.patch("app.crud.equipment.策略数据完整性检验", mock_nothing)

    # 正向
    test_screen_backtest_indicator["收益率"] = 1.23
    test_screen_backtest_indicator.pop("_id")
    data = {"装备回测指标数据": [test_screen_backtest_indicator]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == {"result": "success"}
    # 插入空数据
    data = {"装备回测指标数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备回测指标失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_screen_backtest_indicator.pop("Alpha")
    data = {"装备回测指标数据": [test_screen_backtest_indicator]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_indicator",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_indicator",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_create_timings_backtest_assess(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_insert_equipment_backtest_real_data,
    mocker,
):
    """创建择时装备的回测评级数据"""
    mocker.patch("app.crud.equipment.策略数据完整性检验", mock_nothing)
    # 正向
    test_timing_backtest_assess["回测年份"] = "2019"
    test_timing_backtest_assess.pop("_id")
    data = {"装备回测评级数据": [test_timing_backtest_assess]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == {"result": "success"}
    # 插入空数据
    data = {"装备回测评级数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备回测评级失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_timing_backtest_assess.pop("评级")
    data = {"装备回测评级数据": [test_timing_backtest_assess]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/backtest_assess",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_create_screens_backtest_assess(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_create_equipments,
    fixture_insert_equipment_backtest_real_data,
    mocker,
):
    """创建选股装备的回测评级数据"""
    mocker.patch("app.crud.equipment.策略数据完整性检验", mock_nothing)
    # 正向
    test_screen_backtest_assess[0]["评级"] = "C"
    test_screen_backtest_assess[0].pop("_id")
    data = {"装备回测评级数据": [test_screen_backtest_assess[0]]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == {"result": "success"}
    # 插入空数据
    data = {"装备回测评级数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备回测评级失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_screen_backtest_assess[0].pop("评级")
    data = {"装备回测评级数据": [test_screen_backtest_assess[0]]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_assess",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/backtest_assess",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_create_timings_real_signal(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_insert_equipment_backtest_real_data,
    mocker,
):
    """创建择时装备的实盘信号数据"""
    mocker.patch("app.crud.equipment.策略数据完整性检验", mock_nothing)
    # 正向
    test_timing_real_signal["收益率"] = 1.2
    test_timing_real_signal.pop("_id")
    data = {"装备实盘信号数据": [test_timing_real_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == {"result": "success"}
    # 插入空数据
    data = {"装备实盘信号数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备实盘信号失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_timing_real_signal.pop("收益率")
    data = {"装备实盘信号数据": [test_timing_real_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/timings/real_signal",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_create_screens_real_signal(
    fixture_client,
    fixture_settings,
    free_user_headers,
    airflow_user_headers,
    fixture_insert_equipment_backtest_real_data,
    mocker,
):
    """创建选股装备的实盘信号数据"""
    # 正向
    mocker.patch("app.crud.equipment.策略数据完整性检验", mock_nothing)

    test_screen_real_signal["收益率"] = 1.2
    test_screen_real_signal.pop("_id")
    data = {"装备实盘信号数据": [test_screen_real_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 200
    assert result.json() == {"result": "success"}
    # 插入空数据
    data = {"装备实盘信号数据": []}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 400
    assert result.json() == {"errors": {"body": ["创建装备实盘信号失败，错误原因：传入列表不能为空"]}}
    # 参数错误
    data = {}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 数据缺失
    test_screen_real_signal.pop("收益率")
    data = {"装备实盘信号数据": [test_screen_real_signal]}
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/real_signal",
        json=jsonable_encoder(data),
        headers=airflow_user_headers,
    )
    assert result.status_code == 422
    assert result.json()["detail"][0]["type"] == "value_error.missing"
    # 权限不够
    result = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/screens/real_signal",
        json=jsonable_encoder(data),
        headers=free_user_headers,
    )
    assert result.status_code == 400
    assert "用户权限不足" in result.text


def test_query_store_equipment_list(fixture_client, fixture_settings, free_user_headers, fixture_create_screen_equipment):
    """查询商城内的装备列表"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/store/list?排序=121212",
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json() == {"errors": {"body": ["错误的排序类型"]}}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/store/list?标签=回落转强&search=test_选股装备&昵称",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "数据" in response.json().keys()
    assert "标识符" in response.json()["数据"][0].keys()


def test_check_equipment_exist(fixture_client, fixture_settings, free_user_headers, fixture_create_screen_equipment):
    """查询某装备是否存在"""
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/check_exist/?name=121212",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "failed"}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/check_exist/?name={fixture_create_screen_equipment['名称']}",
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"result": "success"}


def test_query_on_and_off_equipments(fixture_client, fixture_settings, free_user_headers, fixture_create_screen_equipment):
    """筛选已上线和已下线的装备"""
    # wrong
    params = {"排序": "上线时间", "skip": 0, "limit": 10}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/on_and_off/",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.text == '{"errors":{"body":["查询装备排序参数错误，请输入规定的排序方式。详细错误：list index out of range"]}}'
    # right
    params = {"排序": "上线时间=-1", "skip": 0, "limit": 10}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/on_and_off/",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_offline_reason(
    fixture_client,
    fixture_settings,
    free_user_headers,
    vip_user_headers,
    fixture_create_equipments,
):
    """更新某装备的下线原因"""
    sid = fixture_create_equipments[0]["标识符"]
    # wrong
    data = {"下线原因": "下线原因"}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{sid}/offline_reason",
        json=data,
        headers=vip_user_headers,
    )
    assert response.status_code == 403
    assert response.json()["errors"]["body"][0] == f"您没有修改该装备（{sid}）的权限"

    data = {"下线原因": "下线原因"}
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{sid}/offline_reason",
        json=data,
        headers=free_user_headers,
    )
    assert response.status_code == 400
    assert response.text == '{"errors":{"body":["该状态不允许修改下线原因"]}}'
    # right
    data = {"下线原因": "下线原因"}
    db = asyncio.get_event_loop().run_until_complete(get_database())
    asyncio.get_event_loop().run_until_complete(get_equipment_collection(db).update_one({"标识符": sid}, {"$set": {"状态": "已下线"}}))
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{sid}/offline_reason",
        json=data,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["result"] == "success"


def test_query_equipment_user_list(
    fixture_client,
    fixture_settings,
    free_user_headers,
    free_user_data,
    fixture_create_equipments,
):
    """查询装备作者列表"""
    # right
    params = {"状态": "已上线", "评级": "A", "skip": 0, "limit": 100}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/user/list",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "用户" + free_user_data["user"]["mobile"][-4:] in response.json()


def test_get_latest_equipment_real_indicator(fixture_client, fixture_settings, free_user_headers, mocker):
    """查询大类资产/基金定投装备实盘指标数据"""
    # wrong
    sid = "01000000000000"
    start = end = datetime.now()
    params = {"sid": sid, "start": start, "end": end, "skip": 0, "limit": 10}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{sid}/real_indicator",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert "string does not match regex" in response.text
    # right
    mocker.patch("app.crud.equipment.get_collection_by_config", MockConfigCollection)
    start = end = FastTdate.last_tdate(datetime.today()).strftime("%Y-%m-%d")
    sid = "06000000test01"
    params = {"sid": sid, "start": start, "end": end, "skip": 0, "limit": 10}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{sid}/real_indicator",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_latest_equipment_real_data(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_create_equipments,
    mocker,
):
    """查询某装备最新实盘数据"""
    # wrong
    sid = "04000000000000"
    real_type = "real_signal"
    params = {"sid": sid, "real_type": real_type}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{sid}/{real_type}/latest",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == 'string does not match regex "^(06|07)"'
    # right
    mocker.patch("app.crud.equipment.get_collection_by_config", MockConfigCollection)
    mocker.patch("app.crud.equipment.get_equipment_collection", MockEquipmentCollection)
    sid = 大类资产配置实盘指标数据["标识符"]
    real_type = "real_indicator"
    params = {"sid": sid, "real_type": real_type}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/{sid}/{real_type}/latest",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["标识符"] == sid


def test_create_cn_data(fixture_client, fixture_settings, airflow_user_headers, mocker):
    """创建装备的实盘回测数据"""
    # wrong
    equipment_name = "xxx"
    data_type = "real_indicator"
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/{equipment_name}/{data_type}",
        headers=airflow_user_headers,
    )
    assert response.status_code == 422
    msg = 'string does not match regex "^(asset_allocation|aipman)$"'
    assert response.json()["detail"][0]["msg"] == msg
    # # right
    mocker.patch("app.crud.equipment.get_equipment_collection", MockEquipmentCollection)
    mocker.patch("app.crud.equipment.get_collection_by_config", MockConfigCollection)
    equipment_name = "asset_allocation"
    data_type = "real_indicator"
    大类资产配置实盘指标数据.pop("_id")
    #
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/{equipment_name}/{data_type}",
        json=jsonable_encoder({"装备实盘回测数据": []}),
        headers=airflow_user_headers,
    )
    assert response.status_code == 400
    assert response.text == '{"errors":{"body":["创建装备回测信号失败，错误原因：传入列表不能为空"]}}'
    #
    response = fixture_client.post(
        f"{fixture_settings.url_prefix}/equipment/{equipment_name}/{data_type}",
        json=jsonable_encoder({"装备实盘回测数据": [大类资产配置实盘指标数据]}),
        headers=airflow_user_headers,
    )
    assert response.status_code == 200
    assert response.text == '{"result":"success"}'


def test_delete_cn_data(fixture_client, fixture_settings, airflow_user_headers, mocker):
    """删除某装备的实盘回测数据"""
    equipment_name = "asset_allocation"
    data_type = "real_indicator"
    # wrong
    sid = "02000000000000"
    equipment_name = "xxx"
    data_type = "real_indicator"
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/equipment/{equipment_name}/{data_type}/{sid}",
        headers=airflow_user_headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == 'string does not match regex "^(screens|timings|asset_allocation|aipman)$"'
    # right
    mocker.patch("app.crud.equipment.get_collection_by_config", MockConfigCollection)
    sid = 大类资产配置实盘指标数据["标识符"]
    equipment_name = "asset_allocation"
    data_type = "real_indicator"
    response = fixture_client.delete(
        f"{fixture_settings.url_prefix}/equipment/{equipment_name}/{data_type}/{sid}",
        headers=airflow_user_headers,
    )
    assert response.status_code == 200
    assert response.text == '{"result":"success"}'


def test_update_equipment_last_used_time(fixture_client, fixture_settings, vip_user_headers, fixture_create_equipments):
    response = fixture_client.put(
        f"{fixture_settings.url_prefix}/equipment/{fixture_create_equipments[0]['标识符']}/latest",
        headers=vip_user_headers,
    )
    assert response.status_code == 200
    assert response.json()["result"] == "更新成功"


def test_get_grade_strategy_words_by_time_view(
    fixture_client,
    fixture_settings,
    free_user_headers,
    fixture_create_equipments,
    mocker,
):
    mocker.patch("app.service.equipment.get_strategy_signal", mock_get_strategy_signal)
    params = {"sid": "11000000test01", "symbol_list": ["000001", "600519"]}
    response = fixture_client.get(
        f"{fixture_settings.url_prefix}/equipment/stocks/grade_list",
        params=params,
        headers=free_user_headers,
    )
    assert response.status_code == 200
    assert "000001" in [x["symbol"] for x in response.json()]
