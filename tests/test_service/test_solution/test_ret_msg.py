import pytest

from app.service.solutions.ret_msg import market_from_symbol


@pytest.mark.parametrize(
    "symbol, exchange",
    [
        ("000001", "0"),
        ("300001", "0"),
        ("200001", "0"),
        ("080001", "0"),
        ("031001", "0"),
        ("500001", "0"),
        ("510001", "0"),
        ("520001", "0"),
        ("600001", "1"),
        ("900001", "1"),
        ("730001", "1"),
        ("700001", "1"),
        ("580001", "1"),
        ("150001", "1"),
        ("160001", "1"),
        ("180001", "1"),
    ]
)
def test_market_from_symbol(symbol, exchange):
    rv = market_from_symbol(symbol)
    assert exchange == rv
