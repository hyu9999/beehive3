import pytest
from hq2redis import HQSourceError

from app.outer_sys.hq.hq_source.jiantou import JiantouHQ

pytestmark = pytest.mark.asyncio


SYMBOL, EXCHANGE = "601816", "1"


FAKE_HQ_JSON = {
    "result": {
        'symbol': '601816', 'baseDate': '20210319', 'marketCd': '1', 'DJ': '317940584.00', 'sellTotal': '0',
        'sellPrice': '5.630', 'stockUD': '-0.06', 'volumeRatio': '44.52900', 'prevClose': '5.680',
        'originalPrevClose2': '5.68000', 'bestBid1': '5.620', 'execPriceVolume': '0', 'bestBid2': '5.610',
        'bestBid3': '5.600', 'marketVal': '0.00', 'high': '5.690', 'amplitude': '1.41', 'bestBid4': '5.590',
        'originalPrevClose1': '5.68000', 'GAV1': '472700', 'bestBid5': '5.580', 'low': '5.610',
        'GAV3': '550800', 'GAV2': '479100', 'GAV5': '633500', 'quantityRatio': '0.00',
        'datetimeCPP': '202103191500', 'GAV4': '443173', 'GAP1': '5.630', 'totalMarketVal': '0.00',
        'commission': '41408', 'symbolName': '京沪高铁', 'GAP3': '5.650', 'turnover': '',
        'tradeIncrease': '-1.06', 'consecutivePresentPrice': '5.620', 'GAP2': '5', 'GAP5': '5.670',
        'earning': '', 'GAP4': '5.660', 'tradeHalt': '0', 'buyPrice': '5.620', 'originalLow2': '5.61000',
        'buyTotal': '0', 'consecutiveVolume': '56353661', 'calPresentPrice': '5.620', 'symbolTyp': '3',
        'bestBidAmt3': '3621000', 'bestBidAmt4': '1008100', 'bestBidAmt5': '544100',
        'originalClose2': '5.62000', 'bestBidAmt1': '143928', 'bestBidAmt2': '1402900',
        'originalHigh2': '5.69000', 'min5UpDown': '0.17800', 'originalOpen2': '5.65000',
        'averagePrice': '5.64188', 'open': '5.650'
    },
    "status": "OK"
}


class FakeJiantouRequest:

    class FakeResponse:
        def __init__(self, *args, **kwargs):
            self.status_code = 200

        def json(self):
            return FAKE_HQ_JSON

    async def __aexit__(self, *args, **kwargs):
        ...

    async def __aenter__(self, *args, **kwargs):
        return self

    async def get(self, *args, **kwargs):
        return self.FakeResponse()


@pytest.fixture(autouse=True, scope="module")
def jiantou(module_mocker):
    module_mocker.patch("app.outer_sys.hq.hq_source.jiantou.httpx.AsyncClient", side_effect=FakeJiantouRequest)
    return JiantouHQ()


async def test_jiantou_field():
    """测试建投接口是否有变动."""
    json = await JiantouHQ()._fetch(SYMBOL, EXCHANGE)
    for key in FAKE_HQ_JSON["result"].keys():
        assert key in json.keys()


async def test_fetch(jiantou):
    json = await jiantou._fetch(SYMBOL, EXCHANGE)
    assert json["symbol"] == SYMBOL
    assert json["marketCd"] == EXCHANGE


async def test_get_security_info(jiantou):
    with pytest.raises(HQSourceError) as excinfo:
        await jiantou.get_security_info(SYMBOL, EXCHANGE)
    assert "该行情源未提供证券基本信息数据." in str(excinfo.value)


async def test_get_security_price(jiantou):
    json = await jiantou.get_security_price(SYMBOL, EXCHANGE)
    assert json.symbol == SYMBOL
    assert json.exchange == EXCHANGE
    assert float(json.current) == float(FAKE_HQ_JSON["result"]["consecutivePresentPrice"])


async def test_get_security_hq(jiantou):
    json = await jiantou.get_security_hq(SYMBOL, EXCHANGE)
    assert json.symbol == SYMBOL
    assert json.exchange == EXCHANGE
    assert float(json.open) == float(FAKE_HQ_JSON["result"]["open"])


async def test_get_security_ticks(jiantou):
    json = await jiantou.get_security_ticks(SYMBOL, EXCHANGE)
    assert json.symbol == SYMBOL
    assert json.exchange == EXCHANGE
    assert float(json.bid1_p) == float(FAKE_HQ_JSON["result"]["bestBid1"])

