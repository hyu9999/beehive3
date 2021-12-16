from copy import deepcopy
from datetime import datetime
from pandas import Timestamp
from bson import ObjectId
from pytest import mark

from app.crud.portfolio import get_portfolio_by_id
from app.enums.fund_account import Exchange
from app.enums.portfolio import 风险点状态, 风险类型
from app.models.base.portfolio import 风险点信息
from app.models.fund_account import FundAccountInDB, FundAccountPositionInDB
from app.models.portfolio import Portfolio
from app.models.rwmodel import PyObjectId
from app.service.risks.detection import (
    risk_detection_by_robot,
    risk_detection,
    get_detect_all_risks,
    save_risks,
    filter_risks,
    signal_to_risk,
    get_stock_risk,
    get_position_risk,
    get_stock_risk_data,
)
from tests.mocks.equipment import MockEquipmentCollection
from tests.mocks.robot import mock_robot

pytestmark = mark.asyncio


async def test_risk_detection_by_robot(fixture_client, fixture_db, fixture_portfolio, mocker):
    async def mock_risk_detection(*args, **kwargs):
        pass

    mock_func = mocker.patch("app.service.risks.detection.risk_detection", side_effect=mock_risk_detection)
    await risk_detection_by_robot(fixture_db)
    assert mock_func.called


async def test_risk_detection(fixture_client, fixture_db, fixture_portfolio, mocker):
    async def fake_get_fund_asset(*args, **kwargs):
        return []

    async def fake_get_fund_account_position(*args, **kwargs):
        return []

    async def fake_get_detect_all_risks(*args, **kwargs):
        return []

    async def fake_save_risks(*args, **kwargs):
        return []

    mock_get_fund_asset = mocker.patch("app.service.risks.detection.get_fund_asset", side_effect=fake_get_fund_asset)
    mock_get_fund_account_position = mocker.patch("app.service.risks.detection.get_fund_account_position", side_effect=fake_get_fund_account_position)
    mock_get_detect_all_risks = mocker.patch("app.service.risks.detection.get_detect_all_risks", side_effect=fake_get_detect_all_risks)
    mock_save_risks = mocker.patch("app.service.risks.detection.save_risks", side_effect=fake_save_risks)
    await risk_detection(fixture_db, Portfolio(**fixture_portfolio), send_msg=False)
    assert mock_get_fund_asset.called
    assert mock_get_fund_account_position.called
    assert mock_get_detect_all_risks.called
    assert mock_save_risks.called


async def test_get_detect_all_risks(fixture_client, fixture_db, fixture_portfolio, mocker):
    fund_account_assets = FundAccountInDB(capital=500000, assets=500000, cash=500000, ts_data_sync_date=datetime.now())
    stock = []
    fund_account_position = [FundAccountPositionInDB(**x) for x in stock]

    async def fake_create_stralib_robot(*args, **kwargs):
        return

    async def fake_get_stock_risk(*args, **kwargs):
        return []

    async def fake_get_position_risk(*args, **kwargs):
        return []

    async def fake_filter_risks(*args, **kwargs):
        return []

    mock_create_stralib_robot = mocker.patch("app.service.risks.detection.create_stralib_robot", side_effect=fake_create_stralib_robot)
    mock_get_stock_risk = mocker.patch("app.service.risks.detection.get_stock_risk", side_effect=fake_get_stock_risk)
    mock_get_position_risk = mocker.patch("app.service.risks.detection.get_position_risk", side_effect=fake_get_position_risk)
    mock_filter_risks = mocker.patch("app.service.risks.detection.filter_risks", side_effect=fake_filter_risks)
    await get_detect_all_risks(fixture_db, Portfolio(**fixture_portfolio), fund_account_assets, fund_account_position)
    assert mock_create_stralib_robot.called
    assert mock_get_stock_risk.called
    assert mock_get_position_risk.called
    assert mock_filter_risks.called


async def test_save_risks(fixture_client, fixture_db, fixture_portfolio):
    risks = [{"id": ObjectId(), "status": 风险点状态.confirm, "risk_type": 风险类型.underweight, "position_advice": [0.2, 0.6]}]
    all_risks = [风险点信息(**x) for x in risks]
    await save_risks(fixture_db, Portfolio(**fixture_portfolio), all_risks)
    portfolio = await get_portfolio_by_id(fixture_db, PyObjectId(fixture_portfolio["_id"]))
    assert portfolio.risks[0].risk_type == risks[0]["risk_type"]


async def test_filter_risks(fixture_client):
    # 都无风险点
    old_risks, new_risks, fund_account_position = [], [], []
    risks = await filter_risks(new_risks, old_risks, fund_account_position)
    assert len(risks) == 0
    # 之前有风险点，目前没风险点: 覆盖旧的风险点
    old_risk_list = [{"id": ObjectId(), "status": 风险点状态.confirm, "risk_type": 风险类型.underweight, "position_advice": [0.2, 0.6]}]
    old_risks = [风险点信息(**x) for x in old_risk_list]
    risks = await filter_risks(new_risks, old_risks, fund_account_position)
    assert len(risks) == 0
    # 之前无风险点，检查出风险点
    old_risks = []
    new_risk_list = [{"id": ObjectId(), "status": 风险点状态.confirm, "risk_type": 风险类型.underweight, "position_advice": [0.2, 0.6]}]
    new_risks = [风险点信息(**x) for x in new_risk_list]
    risks = await filter_risks(new_risks, old_risks, fund_account_position)
    assert len(risks) == 1
    assert risks[0].id == new_risks[0].id
    # 之前有风险点再次检查出风险点：保持旧的风险点不变
    old_risk_list = [{"id": ObjectId(), "status": 风险点状态.confirm, "risk_type": 风险类型.underweight, "position_advice": [0.2, 0.6]}]
    old_risks = [风险点信息(**x) for x in old_risk_list]
    new_risk_list = [{"id": ObjectId(), "status": 风险点状态.confirm, "risk_type": 风险类型.underweight, "position_advice": [0.2, 0.6]}]
    new_risks = [风险点信息(**x) for x in new_risk_list]
    risks = await filter_risks(new_risks, old_risks, fund_account_position)
    assert len(risks) == 1
    assert risks[0].id == old_risks[0].id


async def test_signal_to_risk(fixture_client, fixture_db, fixture_portfolio):
    signal = {
        "TPRICE": -1.0,
        "TDATE": Timestamp("2021-04-16 00:00:00"),
        "SIGNAL": -1.0,
        "OPERATOR": 7.0,
        "STKEFFEFT": 2300.0,
        "SYMBOL": "600196",
        "MARKET": Exchange.CNSESH,
    }
    risk = await signal_to_risk(fixture_db, signal, Portfolio(**fixture_portfolio))
    assert set(risk.dict().keys()) == {
        "data",
        "date",
        "exchange",
        "id",
        "name",
        "opinion",
        "position_advice",
        "position_rate",
        "price",
        "ratio",
        "risk_type",
        "status",
        "symbol",
        "symbol_name",
    }
    # 个股风险： 达到调仓周期


async def test_get_stock_risk(fixture_client, fixture_db, fixture_portfolio_underweight_risk):
    robot = await mock_robot(Portfolio(**fixture_portfolio_underweight_risk))
    risks = await get_stock_risk(fixture_db, robot, Portfolio(**fixture_portfolio_underweight_risk))
    assert len(risks) == 1
    assert set(risks[0].dict().keys()) == {
        "data",
        "date",
        "exchange",
        "id",
        "name",
        "opinion",
        "position_advice",
        "position_rate",
        "price",
        "ratio",
        "risk_type",
        "status",
        "symbol",
        "symbol_name",
    }


async def test_get_position_risk(fixture_client, fixture_portfolio_underweight_risk, fixture_portfolio_overweight_risk, fixture_portfolio_sci_risk):
    # 仓位过轻
    robot = await mock_robot(Portfolio(**fixture_portfolio_underweight_risk))
    risk = await get_position_risk(robot)
    assert risk.risk_type == 风险类型.underweight
    # 仓位过重
    robot = await mock_robot(Portfolio(**fixture_portfolio_overweight_risk))
    risk = await get_position_risk(robot)
    assert risk.risk_type == 风险类型.overweight
    # 其他
    robot = await mock_robot(Portfolio(**fixture_portfolio_sci_risk))
    risk = await get_position_risk(robot)
    assert risk is None


async def test_get_stock_risk_data(fixture_client, fixture_db, fixture_portfolio_overweight_risk, fixture_portfolio_sci_risk, mocker):
    # 审计意见类型发出了卖出信号
    signal = {
        "TPRICE": -1.0,
        "TDATE": Timestamp("2021-04-16 00:00:00"),
        "SIGNAL": -1.0,
        "OPERATOR": "sjyj01",
        "STKEFFEFT": 4400.0,
        "SYMBOL": "603359",
        "MARKET": Exchange.CNSESH,
    }
    m_get_equipment_collection = mocker.patch("app.service.risks.detection.get_equipment_collection", side_effect=MockEquipmentCollection)
    risk = await get_stock_risk_data(fixture_db, signal)
    assert m_get_equipment_collection.called
    assert risk[0]["name"] == "审核意见"
    # 净有息负债率发出了卖出信号
    signal = {
        "TPRICE": -1.0,
        "TDATE": Timestamp("2021-04-16 00:00:00"),
        "SIGNAL": -1.0,
        "OPERATOR": "yxfz01",
        "STKEFFEFT": 4400.0,
        "SYMBOL": "603359",
        "MARKET": Exchange.CNSESH,
    }
    risk = await get_stock_risk_data(fixture_db, signal)
    assert risk[0]["name"] == "净有息负债率"
    # 被ST股票发出了卖出信号
    signal = {
        "TPRICE": -1.0,
        "TDATE": Timestamp("2021-04-16 00:00:00"),
        "SIGNAL": -1.0,
        "OPERATOR": "st0001",
        "STKEFFEFT": 4400.0,
        "SYMBOL": "603359",
        "MARKET": Exchange.CNSESH,
    }
    risk = await get_stock_risk_data(fixture_db, signal)
    assert risk[0]["name"] == "被ST时间"
    # 潜在ST股票发出了卖出信号
    signal = {
        "TPRICE": -1.0,
        "TDATE": Timestamp("2021-04-16 00:00:00"),
        "SIGNAL": -1.0,
        "OPERATOR": "pst001",
        "STKEFFEFT": 4400.0,
        "SYMBOL": "603359",
        "MARKET": Exchange.CNSESH,
    }
    risk = await get_stock_risk_data(fixture_db, signal)
    assert risk[0]["name"] == "股东权益"
    # 交易算法发出了卖出信号
    signal = {
        "TPRICE": -1.0,
        "TDATE": Timestamp("2021-04-16 00:00:00"),
        "SIGNAL": -1.0,
        "OPERATOR": "8",
        "STKEFFEFT": 4400.0,
        "SYMBOL": "603359",
        "MARKET": Exchange.CNSESH,
    }
    risk = await get_stock_risk_data(fixture_db, signal)
    assert risk[0]["name"] == "建议卖出价"
