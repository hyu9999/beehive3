from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app.models.user import User
from tests.consts.robots import robot_test_data


class MockRconfig:
    reduce = None


class MockRobot:
    def __init__(
        self,
        current_position,
        all_risk_list,
        reduce_programme=None,
        reduce_final_position=0,
        add_programme=None,
        final_position=45,
        recommend_stocks_dict=None,
        buy_programme=None,
    ):
        self.current_position = current_position
        self.all_risk_list = all_risk_list
        self.timing_signal = "40-500"
        self.reduce_programme = reduce_programme
        self.reduce_final_position = reduce_final_position
        self.add_programme = add_programme
        self.final_position = final_position
        self.recommend_stocks_dict = recommend_stocks_dict
        self.buy_programme = buy_programme

    @staticmethod
    def get_hold_risk():
        pass

    @staticmethod
    def check_position():
        pass

    @staticmethod
    def reduce_position():
        pass

    @staticmethod
    def tb_add_position():
        pass

    @staticmethod
    def get_recommend_stocks():
        pass

    @staticmethod
    def get_buy_programme(symbols):
        pass

    @property
    def _rconfig(self):
        return MockRconfig()


async def mock_robot(*args, **kwargs):
    """
    模拟机器人
    mock对象: app.service.solutions.utils.get_robot
    机器人推荐的仓位为40~50%

    Parameters
        args: (PortfolioInResponse, List[SolutionOrderItem])

    Examples:
        mocker.patch("app.service.solutions.solution_list.get_robot", side_effect=mock_robot)
    """

    portfolio = args[0]
    portfolio_name = portfolio.name
    portfolio_risks = [dict(risk) for risk in portfolio.risks]
    # 把风险点中的字段转化为stralib库中的字段
    for risk in portfolio_risks:
        risk["SYMBOL"] = risk["symbol"]
        risk["MARKET"] = "CNSESH" if risk["exchange"] == "1" else "CNSESZ"
        risk["STKEFFEFT"] = 1000
        risk["TDATE"] = datetime.utcnow().strftime("%Y%m%d")
        # 1 = 卖
        risk["SIGNAL"] = 1
        risk["TPRICE"] = 10
        # OPERATOR 为stralib风险类型 对照 app/service/risk/utils.py/operator_risk_type_mapping
        if risk["risk_type"].value == "5":
            risk["OPERATOR"] = "st0001"
        elif risk["risk_type"].value == "10":
            risk["OPERATOR"] = 5
        elif risk["risk_type"].value == "0":
            risk["OPERATOR"] = 6
        elif risk["risk_type"].value == "1":
            risk["OPERATOR"] = 7
        elif risk["risk_type"].value == "9":
            risk["OPERATOR"] = 9
    # 通过组合的名字来判断风险类型从而初始化robot, 可以用来调整仓位
    # 止盈止损、调仓周期、个股风险组合
    if portfolio_name == "test_portfolio_sci":
        return MockRobot(current_position=0.45, all_risk_list=portfolio_risks)
    # 仓位过重风险组合
    elif portfolio_name == "test_portfolio_overweight":
        # 同比例减仓订单
        reduce_programme_data = [
            {
                "SYMBOL": "600100",
                "MARKET": "CNSESH",
                "STKEFFEFT": 10,
                "TDATE": "TDATE",
                "SIGNAL": -1,
                "OPERATOR": "sell",
                "TPRICE": "10",
            }
        ]
        return MockRobot(current_position=0.9, all_risk_list=portfolio_risks, reduce_programme=reduce_programme_data)
    # 仓位过轻风险组合
    elif portfolio_name == "test_portfolio_underweight":
        # 同比例加仓订单
        add_programme_data = [
            {
                "SYMBOL": "600100",
                "MARKET": "CNSESH",
                "STKEFFEFT": 10,
                "TDATE": "TDATE",
                "SIGNAL": -1,
                "OPERATOR": "buy",
                "TPRICE": "10",
            }
        ]
        return MockRobot(current_position=0.1, all_risk_list=portfolio_risks, add_programme=add_programme_data, recommend_stocks_dict={"600100": "12345"})
    # 买入新股票组合
    elif portfolio_name == "test_portfolio_new_stock":
        buy_programme_data = [
            {
                "SYMBOL": "600100",
                "MARKET": "CNSESH",
                "STKEFFEFT": 10,
                "TDATE": "TDATE",
                "SIGNAL": -1,
                "OPERATOR": "buy",
                "TPRICE": "10",
            }
        ]
        return MockRobot(current_position=0.45, all_risk_list=portfolio_risks, buy_programme=buy_programme_data)
    return MockRobot(current_position=0.45, all_risk_list=portfolio_risks)


async def mock_get_client_robot_list(conn: AsyncIOMotorClient, query: dict, user: User = None):
    return [robot_test_data]


async def mock_empty_client_robot_list(conn: AsyncIOMotorClient, query: dict, user: User = None):
    return []


async def mock_check_strategy_exist_with_true(conn: AsyncIOMotorClient, username: str):
    return True


async def mock_check_strategy_exist_with_false(conn: AsyncIOMotorClient, username: str):
    return False
