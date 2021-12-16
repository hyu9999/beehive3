import copy
from datetime import datetime

from pytest import fixture

from app.enums.solution import SolutionTypeEnum
from tests.mocks.robot import mock_robot
from app.models.rwmodel import PyObjectId


@fixture
def modified_orders_data():
    data = [
        {
            "symbol": "600100",
            "exchange": "1",
            "symbol_name": "测试股票",
            "order_id": "string",
            "fund_id": "string",
            "status": "0",
            "finished_quantity": 0,
            "average_price": 0,
            "quantity": 0,
            "operator": "buy",
            "price": 0,
            "reason": "string",
            "date": "string",
            "opinion": "string",
        }
    ]
    return data


async def mock_order_name_symbol(*args, **kwargs):
    """
    模拟补齐订单中股票名称
    mock对象: app.outer_sys.stralib.robot.utils.order_name_symbol

    Parameters
        args: ([SolutionOrderItem])

    Examples:
        mocker.patch("app.service.solutions.solution_list.order_name_symbol", side_effect=mock_order_name_symbol)
    """
    return args[0]


@fixture(autouse=True)
def robot_mocker(module_mocker):
    module_mocker.patch("app.service.solutions.solution.get_robot", side_effect=mock_robot)
    # module_mocker.patch("app.service.solutions.solution.latest_account_data", side_effect=mock_portfolio_time_series_data)
    # module_mocker.patch("app.service.solutions.solution_list.order_name_symbol", side_effect=mock_order_name_symbol)

    # module_mocker.patch("app.service.risks.risk.get_robot", side_effect=mock_robot)
    return module_mocker


def test_sci_risk_solution(fixture_client, fixture_settings, vip_user_headers, fixture_portfolio_sci_risk):
    """
    测试止盈止损、调仓周期、个股风险解决方案
    解决方案为生成股票卖单
    """
    data = {"portfolio_id": fixture_portfolio_sci_risk["_id"]}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/solutions", json=data, headers=vip_user_headers)
    assert response.status_code == 200
    solution = response.json()
    assert solution["title"] == "止盈止损、调仓周期、个股风险的解决方案"
    assert len(solution["solutions"]) == 1
    assert solution["solutions"][0]["solution_type"] == SolutionTypeEnum.SIMPLE.value
    assert len(solution["solutions"][0]["orders"]) == 2


def test_overweight_risk_solution(fixture_client, fixture_settings, vip_user_headers, modified_orders_data, fixture_portfolio_overweight_risk):
    """测试仓位过重风险解决方案"""
    data = {"portfolio_id": fixture_portfolio_overweight_risk["_id"], "modified_orders": modified_orders_data}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/solutions", json=data, headers=vip_user_headers)
    assert response.status_code == 200
    solution = response.json()
    assert solution["title"] == "仓位过重的解决方案"
    assert len(solution["solutions"]) == 3
    assert solution["solutions"][0]["solution_type"] == SolutionTypeEnum.SCALE_DOWN.value
    assert solution["solutions"][1]["solution_type"] == SolutionTypeEnum.ROGUING.value
    assert solution["solutions"][2]["solution_type"] == SolutionTypeEnum.CUSTOMIZE.value


def test_underweight_risk_solution(fixture_client, fixture_settings, vip_user_headers, modified_orders_data, fixture_portfolio_underweight_risk):
    """测试仓位过轻风险解决方案"""
    data = {"portfolio_id": fixture_portfolio_underweight_risk["_id"], "modified_orders": modified_orders_data}
    response = fixture_client.post(f"{fixture_settings.url_prefix}/solutions", json=data, headers=vip_user_headers)
    assert response.status_code == 200
    solution = response.json()
    assert solution["title"] == "仓位过轻的解决方案"
    assert len(solution["solutions"]) == 2
    assert solution["solutions"][0]["solution_type"] == SolutionTypeEnum.SCALE_UP.value
    assert solution["solutions"][1]["solution_type"] == SolutionTypeEnum.NEW_STOCKS.value


def test_new_stocks_solution(fixture_client, fixture_settings, vip_user_headers, fixture_portfolio_new_stock, modified_orders_data):
    """测试买入新股票解决方案"""
    data = {
        "portfolio_id": fixture_portfolio_new_stock["_id"],
        "modified_orders": modified_orders_data,
        "solutions_steps": [3],
        "solutions_types": [4],
    }
    response = fixture_client.post(f"{fixture_settings.url_prefix}/solutions", json=data, headers=vip_user_headers)
    assert response.status_code == 200
    solution = response.json()
    assert solution["title"] == "确认买入新股票"
    assert len(solution["solutions"]) == 1
    assert solution["solutions"][0]["solution_type"] == SolutionTypeEnum.SIMPLE.value


def test_end_solution(fixture_client, fixture_settings, vip_user_headers, fixture_portfolio, modified_orders_data):
    """测试最终解决方案"""
    data = {
        "portfolio_id": fixture_portfolio["_id"],
        "modified_orders": modified_orders_data,
        "solutions_types": [4],
    }
    response = fixture_client.post(f"{fixture_settings.url_prefix}/solutions", json=data, headers=vip_user_headers)
    assert response.status_code == 200
    solution = response.json()
    assert solution["title"] == "最终解决方案"
    assert len(solution["solutions"]) == 1
    assert solution["solutions"][0]["solution_type"] == SolutionTypeEnum.SIMPLE.value


def test_solution(fixture_client, fixture_settings, vip_user_headers, fixture_portfolio, modified_orders_data):
    """测试已全部解决"""
    data = {
        "portfolio_id": fixture_portfolio["_id"],
        "modified_orders": [],
        "solutions_types": [4],
    }
    response = fixture_client.post(f"{fixture_settings.url_prefix}/solutions", json=data, headers=vip_user_headers)
    assert response.status_code == 200
    solution = response.json()
    assert solution["title"] == "最终解决方案"
    assert len(solution["solutions"]) == 0
    assert solution["status"] == "没有风险点, 无需解决方案"
