import pytest
import pandas as pd
from hq2redis import HQSourceError
from pytest import mark

from app.service.stocks.stock import query_stock_price_from_jiantou, query_realtime_from_data_source, get_stock_list_from_stralib
from tests.test_outer_sys.test_hq.test_hq_source.test_jiantou import FakeJiantouRequest, FAKE_HQ_JSON


pytestmark = pytest.mark.asyncio


async def test_query_stock_price_from_jiantou(mocker):
    async def foo(*args, **kwargs):
        return "foo"

    mocker.patch("app.service.stocks.stock.query_realtime_from_data_source", side_effect=foo)
    result = await query_stock_price_from_jiantou(["x_y"])
    assert result == ["foo"]

    async def bar(*args, **kwargs):
        raise HQSourceError

    mocker.patch("app.service.stocks.stock.query_realtime_from_data_source", side_effect=bar)
    result = await query_stock_price_from_jiantou(["x_y"])
    assert not result


async def test_query_realtime_from_data_source(mocker):
    mocker.patch("app.service.stocks.stock.httpx.AsyncClient", side_effect=FakeJiantouRequest)
    result = await query_realtime_from_data_source(symbol="foo", marketid=0)
    assert result["symbol"] == FAKE_HQ_JSON["result"]["symbol"]


def fake_get_version_data(table_name: str):
    if table_name == "md_sec_type":
        data = {
            "UPDATE_TIME": ["2015-06-25 15:31:33", "2020-12-01 09:15:04", "2015-06-25 15:31:33", "2020-12-01 09:15:04"],
            "SYMBOL": ["000001", "000002", "000001", "000002"],
            "EXCHANGE": ["CNSESZ", "CNSESZ", "CNSESZ", "CNSESZ"],
            "ID": ["1", "2", "1", "2"],
            "SECURITY_ID": ["2", "4", "2", "4"],
            "SEC_SHORT_NAME": ["平安银行", "万科A", "平安银行", "万科A"],
            "TYPE_ID": ["101001001001", "101001001001", "101001001001", "101001001001"],
            "TYPE_NAME": ["申万二级行业指数", "申万二级行业指数", "全部A股", "全部A股"],
            "INFO_DATE": ["1991-04-03", "1991-04-03", "1991-04-03", "1991-04-03"],
            "OUT_DATE": ["NaN", "NaN", "NaN", "NaN"],
            "TMSTAMP": [5254532936, 5254532936, 5254532936, 5254532936],
        }
        return pd.DataFrame(data=data)
    elif table_name == "idx_cons":
        data = {
            "INFO_DATE": ["1999-11-10", "1998-01-22"],
            "SYMBOL": ["000001", "000002"],
            "EXCHANGE": ["CNSESH", "CNSESH"],
            "ID": ["351953", "351953"],
            "SECURITY": ["1", "1"],
            "CONS_ID": ["584", "585"],
            "OUT_DATE": ["2009-12-30", "2006-04-25"],
            "IS_NEW": [1, 1],
            "UPDATE_TIME": ["2017-11-30", "2016-01-13"],
            "TMSTAMP": [33619468815, 33619468816],
            "SECURITY_ID": ["2", "4"],
        }
        return pd.DataFrame(data=data)
    elif table_name == "md_security":
        data = {
            "UPDATE_TIME": ["2017-11-30", "2016-01-13"],
            "SYMBOL": ["000001", "000002"],
            "EXCHANGE": ["CNSESH", "CNSESH"],
            "SECURITY_ID": ["2", "4"],
            "SEC_FULL_NAME": ["平安银行股份有限公司", "万科企业股份有限公司"],
            "SEC_SHORT_NAME": ["平安银行", "万科A"],
            "CN_SPELL": ["PAYH", "WKA"],
            "SEC_FULL_NAME_EN": ["Ping An Bank Co., Ltd.", "China VanKe Co., Ltd."],
            "DYID": ["PAB", "Vanke"],
        }
        return pd.DataFrame(data=data)


@mark.skip
async def test_get_stock_list_from_stralib(mocker):
    mocker.patch("app.service.stocks.stock.get_version_data", side_effect=fake_get_version_data)
    result = get_stock_list_from_stralib()
    assert len(result) == 2
    assert list(result[0].keys()) == ["symbol", "exchange", "symbol_shortname", "symbol_name", "industry"]
