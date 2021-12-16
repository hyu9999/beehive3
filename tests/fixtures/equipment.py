from datetime import datetime

from pytest import fixture, mark

from app.db.mongodb import get_database
from app.service.strategy_data import delete_adam_strategy_signal
from tests.consts.backtest import (
    test_timing_backtest_indicator,
    test_screen_backtest_indicator,
    test_timing_backtest_signal,
    test_screen_backtest_signal,
    test_timing_backtest_assess,
    test_screen_backtest_assess,
    test_timing_real_signal,
    test_screen_real_signal,
    test_大类资产实盘信号_real_signal,
)
from tests.consts.equipment import screen_test_data_with_mfrs
from tests.mocks.topic import MockDisc, mock_create_thread

pytestmark = mark.asyncio


@fixture
def risk_equipments_data(free_user_data):
    """风控装备数据"""
    data = [
        {
            "名称": "test_短期走势",
            "作者": free_user_data["user"]["username"],
            "分类": "风控",
            "状态": "已上线",
            "标签": ["移动平均线", "技术指标"],
            "英文名": "DQZS_riskman",
            "标识符": "04000000test01",
            "简介": "走势破位，即股价跌破重要技术支撑位，此前趋势发生逆转，开始进入新的相反方向趋势运行的情况。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": "2019-01-01T00:00:00.000+0000",
            "计算时间": "2019-11-21T08:18:28.187+0000",
            "评级": "D",
            "运行天数": 0,
            "累计产生信号数": 0,
            "累计服务人数": 0,
            "创建时间": "2018-12-01T03:40:02.393+0000",
            "可见模式": "完全公开",
            "信号传入方式": "源代码传入",
        },
        {
            "名称": "test_空头行情",
            "作者": free_user_data["user"]["username"],
            "分类": "风控",
            "状态": "已上线",
            "标签": ["移动平均线", "技术指标"],
            "英文名": "KTHQ_riskman",
            "标识符": "04000000test02",
            "简介": "股价中长期走势呈下跌趋势，空头行情股价变化的特征是一连串的大跌小涨。 ",
            "主页地址": "http://bbs.jinniuai.com/t/topic/59",
            "上线时间": "2019-01-01T00:00:00.000+0000",
            "计算时间": "2019-11-21T08:18:28.187+0000",
            "评级": "A",
            "运行天数": 0,
            "累计产生信号数": 0,
            "累计服务人数": 0,
            "创建时间": "2018-12-01T03:40:02.393+0000",
            "可见模式": "完全公开",
            "信号传入方式": "源代码传入",
        },
    ]
    return data


@fixture
def create_risk_equipments(fixture_client, fixture_settings, fixture_db, risk_equipments_data):
    result = fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].find_one({"标识符": risk_equipments_data[0]["标识符"]})
    if not result:
        result = fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].insert_one(risk_equipments_data[0])
        assert result is not None
    result = fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].find_one({"标识符": risk_equipments_data[1]["标识符"]})
    if not result:
        result = fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].insert_one(risk_equipments_data[1])
        assert result is not None
    yield risk_equipments_data
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].delete_many({"名称": {"$regex": "^test"}})


@fixture
def off_line_risk_equipment_in_db(free_user_data):
    """下线的风控装备数据"""
    return {
        "名称": "test_下线风控",
        "作者": free_user_data["user"]["username"],
        "分类": "风控",
        "状态": "已下线",
        "标签": ["移动平均线", "技术指标"],
        "英文名": "DQZS_riskman",
        "标识符": "04000000offl01",
        "简介": "走势破位，即股价跌破重要技术支撑位，此前趋势发生逆转，开始进入新的相反方向趋势运行的情况。",
        "主页地址": "http://bbs.jinniuai.com",
        "上线时间": "2019-01-01T00:00:00.000+0000",
        "计算时间": "2019-11-21T08:18:28.187+0000",
        "评级": "D",
        "运行天数": 0,
        "累计产生信号数": 0,
        "累计服务人数": 0,
        "创建时间": "2018-12-01T03:40:02.393+0000",
        "可见模式": "完全公开",
        "信号传入方式": "源代码传入",
    }


@fixture
def fixture_off_line_risk_equipment(fixture_client, fixture_settings, fixture_db, off_line_risk_equipment_in_db):
    """已下线的风控装备"""
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].insert_one(off_line_risk_equipment_in_db)
    yield off_line_risk_equipment_in_db
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].delete_one({"标识符": off_line_risk_equipment_in_db["标识符"]})


@fixture
def fixture_equipment_in_create_list():
    """创建装备数据列表"""
    return [
        {
            "名称": "test_选股装备",
            "分类": "选股",
            "标签": ["移动平均线", "技术指标"],
            "英文名": "TEST_screen",
            "简介": "对均线和成交量进行评",
            "主页地址": "http://bbs.jinniuai.com",
            "信号传入方式": "源代码传入",
            "源代码": "12121212",
            "可见模式": "完全公开",
            "文章标识符": "1635",
        },
        {
            "名称": "test_择时装备",
            "分类": "择时",
            "标签": ["移动平均线", "技术指标"],
            "英文名": "TEST_screen",
            "简介": "对均线和成交量进行评",
            "主页地址": "http://bbs.jinniuai.com",
            "信号传入方式": "接口传入",
            "可见模式": "完全公开",
        },
        {
            "包": {
                "名称": "test_风控包",
                "分类": "风控包",
                "标签": ["测试", "测试1"],
                "英文名": "TEST_screen2",
                "简介": "对均线和成交量进行评",
                "主页地址": "http://bbs.jinniuai.com",
                "信号传入方式": "手动传入",
                "可见模式": "完全公开",
                "装备列表": ["02190527bdsz02", "02180706roe001", "02180706ra0001"],
            }
        },
    ]


@fixture
def screen_equipment_data(free_user_data):
    """选股装备数据"""
    data = {
        "名称": "test_选股装备",
        "作者": free_user_data["user"]["username"],
        "分类": "选股",
        "标签": ["回落转强", "技术指标"],
        "英文名": "TEST_screen",
        "简介": "对均线和成交量进行评",
        "主页地址": "http://bbs.jinniuai.com",
        "信号传入方式": "接口传入",
        "可见模式": "完全公开",
    }
    return data


@fixture
def fixture_create_screen_equipment(fixture_client, fixture_settings, fixture_db, vip_user_headers, screen_equipment_data, mocker):
    """调用接口创建选股装备"""
    mocker.patch("app.settings.discuzq", MockDisc())
    mocker.patch("app.crud.equipment.create_thread", mock_create_thread)
    response = fixture_client.post(f"{fixture_settings.url_prefix}/equipment/new", json=screen_equipment_data, headers=vip_user_headers)
    assert response.status_code == 201
    screen_equipment_data["标识符"] = response.json()["标识符"]
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].update_one(
        {"标识符": screen_equipment_data["标识符"]}, {"$set": {"状态": "已上线", "评级": "A"}}
    )
    yield screen_equipment_data
    fixture_db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].delete_many({"标识符": response.json()["标识符"]})


@fixture
def equipments_data_in_db(free_user_data):
    """各类型装备数据"""
    data = [
        {
            "标识符": "02000000test01",
            "名称": "test新奇大师选股",
            "简介": "nicaiwocainicaibucai",
            "主页地址": "http://bbs.jinniuai.com",
            "作者": free_user_data["user"]["username"],
            "分类": "选股",
            "状态": "审核中",
            "标签": ["价值投资"],
            "英文名": "null",
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "上线时间": datetime(2019, 12, 18),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "运行天数": 0,
            "累计服务人数": 0,
            "累计产生信号数": 0,
            "源代码": "null",
            "最近使用时间": datetime(2019, 12, 18),
        },
        {
            "标识符": "02000000test02",
            "作者": free_user_data["user"]["username"],
            "名称": "test费雪大师选股",
            "状态": "已上线",
            "分类": "选股",
            "标签": ["成长"],
            "英文名": "Fisher_screen",
            "简介": "根据费雪大师的选股思想，以市收率为核心选出优质成长股。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "A",
            "运行天数": 322,
            "累计产生信号数": 1958,
            "累计服务人数": 7,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test一阳穿多均",
            "作者": free_user_data["user"]["username"],
            "分类": "选股",
            "状态": "已下线",
            "标签": ["成长"],
            "英文名": "MaVol_screen",
            "标识符": "02000000test03",
            "简介": "对均线和成交量进行评级选股。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "A",
            "运行天数": 260,
            "累计产生信号数": 1161,
            "累计服务人数": 2,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test巴菲特选股",
            "作者": free_user_data["user"]["username"],
            "分类": "选股",
            "状态": "审核未通过",
            "标签": ["成长"],
            "英文名": "BFTJZ_screen",
            "标识符": "02000000test04",
            "简介": "基于巴菲特估值思想，选取在行业中基本面较好，且估值最低的5支股票",
            "主页地址": "http://bbs.jinniuai.com/t/topic/73",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "B",
            "运行天数": 324,
            "累计产生信号数": 1080,
            "累计服务人数": 11,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test有息负债率",
            "作者": free_user_data["user"]["username"],
            "分类": "选股",
            "状态": "已上线",
            "标签": ["成长"],
            "英文名": "YXFZL_riskman",
            "标识符": "02000000test05",
            "简介": "净有息负债率是净有息负债占总债务的比率，比率越低，证明企业举债成本越低，相对来说利润也就会提高。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "A",
            "运行天数": 324,
            "累计产生信号数": 27780,
            "累计服务人数": 51,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "标识符": "02000000test06",
            "作者": free_user_data["user"]["username"],
            "名称": "test大师选股",
            "状态": "已上线",
            "分类": "选股",
            "标签": ["成长"],
            "英文名": "Fisher_screen",
            "简介": "根据费雪大师的选股思想，以市收率为核心选出优质成长股。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "A",
            "运行天数": 320,
            "累计产生信号数": 198,
            "累计服务人数": 7,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test量价择时",
            "作者": free_user_data["user"]["username"],
            "分类": "择时",
            "状态": "审核中",
            "标签": ["成长"],
            "英文名": "volumeclose_timing",
            "标识符": "03000000test01",
            "简介": "当短期均线在长期均线之下且成交量相对缩小时仓位为0%,在长期均线之下且成交量相对放大时仓位为0.25,在长期均线之上且成交量相对缩小时仓位为75%,在长期均线之上且成交量相对放大时仓位为100%。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": datetime(2019, 1, 1),
            "评级": "B",
            "运行天数": 0,
            "累计产生信号数": 10,
            "累计服务人数": 0,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "指数列表": ["000300", "399001", "000001", "000905", "399006"],
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test巴菲特择时",
            "作者": free_user_data["user"]["username"],
            "分类": "择时",
            "状态": "已上线",
            "标签": ["成长"],
            "英文名": "BFT_timing",
            "标识符": "03000000test02",
            "简介": "巴菲特择时要求仓位一直保持满仓。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "D",
            "运行天数": 324,
            "累计产生信号数": 216,
            "累计服务人数": 10,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test多空综合",
            "作者": free_user_data["user"]["username"],
            "分类": "择时",
            "状态": "已下线",
            "标签": ["成长"],
            "英文名": "singlechannel_robot3",
            "标识符": "03000000test03",
            "简介": "计算中期周期的均线缠绕指标，当缠绕指标超过临界值时，表示趋势强，均线的排列打分用短周期，否则表示趋势弱，均线的排列打分用长周期,根据均线的排列打分确定仓位建议。",
            "主页地址": "http://bbs.jinniuai.com/t/topic/52",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "A",
            "运行天数": 324,
            "累计产生信号数": 218,
            "累计服务人数": 26,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test成分股",
            "作者": free_user_data["user"]["username"],
            "分类": "择时",
            "状态": "审核未通过",
            "标签": ["成长"],
            "英文名": "component_timing",
            "标识符": "03000000test04",
            "简介": "综合考虑指数及其成分股的行情",
            "主页地址": "http://bbs.jinniuai.com/t/topic/49",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "B",
            "运行天数": 324,
            "累计产生信号数": 219,
            "累计服务人数": 0,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "test盖茨比择时",
            "作者": free_user_data["user"]["username"],
            "分类": "择时",
            "状态": "已上线",
            "标签": ["成长"],
            "英文名": "BFT_timing",
            "标识符": "03000000test05",
            "简介": "盖茨比择时要求仓位一直保持满仓。",
            "主页地址": "http://bbs.jinniuai.com",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "D",
            "运行天数": 315,
            "累计产生信号数": 220,
            "累计服务人数": 10,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "名称": "testST股票",
            "作者": free_user_data["user"]["username"],
            "分类": "风控",
            "状态": "已上线",
            "标签": ["成长"],
            "英文名": "ST_riskman",
            "标识符": "04000000test01",
            "简介": "沪深交易所规定对财务状况或其他状况出现异常的上市公司股票交易进行特别处理，并在简称前冠以‘ST’，这类股票称为ST股，该类股票存在投资风险，如果加上*ST那么就是该股票有退市风险，希望警惕的意思。",
            "主页地址": "http://bbs.jinniuai.com/t/topic",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "A",
            "运行天数": 324,
            "累计产生信号数": 25304,
            "累计服务人数": 51,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
            "最近使用时间": datetime(2019, 1, 1),
            "策略话术": "策略话术",
        },
        {
            "名称": "test风控一号",
            "标识符": "11000000test01",
            "主页地址": "http://bbs.jinniuai.com",
            "作者": free_user_data["user"]["username"],
            "分类": "风控包",
            "状态": "已上线",
            "标签": ["技术风险", "基本面风险"],
            "上线时间": datetime(2019, 1, 1),
            "简介": "本风控包包含以下功能：1、股票出现走势破位；2、股票出现空头行情；3、股票出现潜在ST的情况； 4、审计意见类型有风险； 5、已经被ST的股票; 6、净有息负债率风险。",
            "详细介绍": "暂无",
            "计算时间": datetime(2019, 11, 21),
            "服务了多少组合": 0,
            "运行天数": 638,
            "累计入选股票数量": 0,
            "累计服务人数": 68,
            "装备列表": [
                "04000000test01",
            ],
            "累计产生信号数": 279680,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "可见模式": "完全公开",
            "订阅人数": 11,
            "评级": "A",
            "文章标识符": 1888,
            "最近使用时间": datetime(2019, 1, 1),
        },
        {
            "标识符": "02000000test10",
            "一级分类": "目标筛选",
            "二级分类": "选ETF",
            "作者": free_user_data["user"]["username"],
            "创建时间": datetime(2019, 1, 1),
            "上线时间": datetime(2019, 1, 1),
            "可连接装备类型": ["股票池", "持仓"],
            "可选择触发器列表": ["事件触发器", "时间触发器"],
            "名称": "test估值偏离交易装备",
            "推荐搭配": ["持仓", "股票池"],
            "标签": ["ETF", "估值"],
            "版本": "0.0.1",
            "状态": "已上线",
            "简介": "通过判断ETF所跟踪的指数的估值情况来判断买入和卖出，估值低买入，估值高卖出。",
            "装备库版本": "3.3",
            "详细说明": {
                "简介": "此选股装备以市盈率和成交额作为参考指标。先以最近5年全市场市盈率为参考点，选出当前市盈率位于参考点40% 以下的ETF，再从中筛选出连续10个交易日成交额均大于1千万的ETF。",
                "特点": "此装备选出的ETF处于近五年较低的位置，具有一定的安全边际，不必过于担心被套牢。但在买入时市场还处于预热阶段，因此需要耐心等待市场出现转机。",
                "适用人群": "适合进行中长线投资稳健型的投资者",
                "使用方法": "设定数据源,根据装备参数和触发条件进行相应选股操作。",
            },
            "说明": "通过判断ETF所跟踪的指数的估值情况来判断买入和卖出，估值低买入，估值高卖出。",
            "配置参数": {
                "估值指标": {"default": "pe_ttm", "可选值": ["pe_ttm", "pb"]},
                "高估的标准": {"default": 0.8, "min": 0.5, "max": 1},
                "低估的标准": {"default": 0.2, "min": 0.1, "max": 0.5},
            },
        },
        {
            "名称": "test大类资产配置",
            "作者": free_user_data["user"]["username"],
            "分类": "大类资产配置",
            "状态": "已上线",
            "标签": ["量化投资"],
            "标识符": "06000000test10",
            "简介": "沪深交易所规定对财务状况或其他状况出现异常的上市公司股票交易进行特别处理，并在简称前冠以‘ST’，这类股票称为ST股，该类股票存在投资风险，如果加上*ST那么就是该股票有退市风险，希望警惕的意思。",
            "主页地址": "http://bbs.jinniuai.com/t/topic",
            "上线时间": datetime(2019, 1, 1),
            "计算时间": datetime(2019, 11, 21),
            "评级": "A",
            "运行天数": 11,
            "累计产生信号数": 111,
            "累计服务人数": 11,
            "创建时间": datetime(2018, 12, 1, 3, 40, 2),
            "信号传入方式": "源代码传入",
            "可见模式": "完全公开",
        },
    ]
    return data


@fixture
async def fixture_create_equipments(fixture_settings, equipments_data_in_db):
    """创建多条装备数据"""
    db = await get_database()
    result = await db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].insert_many(equipments_data_in_db)
    assert result is not None
    yield equipments_data_in_db
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].delete_many({"名称": {"$regex": "^test"}})


@fixture
async def fixture_screen_equipment_with_manual_transfer(fixture_settings, client_user_data):
    db = await get_database()
    screen_test_data_with_mfrs["作者"] = client_user_data["user"]["username"]
    result = await db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].insert_one(screen_test_data_with_mfrs)
    assert result is not None
    yield screen_test_data_with_mfrs
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.EQUIPMENT].delete_one({"标识符": screen_test_data_with_mfrs["标识符"]})
    delete_adam_strategy_signal(screen_test_data_with_mfrs["标识符"])

@fixture
async def fixture_insert_equipment_backtest_real_data(fixture_settings, fixture_create_equipments):
    db = await get_database()
    try:
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_INDICATOR_TIMING].insert_one(test_timing_backtest_indicator)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_INDICATOR_SCREEN].insert_one(test_screen_backtest_indicator)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_SIGNAL_TIMING].insert_one(test_timing_backtest_signal)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_SIGNAL_SCREEN].insert_one(test_screen_backtest_signal)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_ASSESSMENT_TIMING].insert_one(test_timing_backtest_assess)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_ASSESSMENT_SCREEN].insert_many(test_screen_backtest_assess)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_SIGNAL_TIMING].insert_one(test_timing_real_signal)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_SIGNAL_SCREEN].insert_one(test_screen_real_signal)
        await db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_SIGNAL_AIP].insert_one(test_大类资产实盘信号_real_signal)
    except Exception as e:
        pass
    else:
        yield fixture_create_equipments
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_INDICATOR_TIMING].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_INDICATOR_SCREEN].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_SIGNAL_TIMING].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_SIGNAL_SCREEN].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_ASSESSMENT_TIMING].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.BACKTEST_ASSESSMENT_SCREEN].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_SIGNAL_TIMING].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_SIGNAL_SCREEN].delete_many({"标识符": {"$regex": "test"}})
    await db[fixture_settings.db.DB_NAME][fixture_settings.collections.REAL_SIGNAL_AIP].delete_many({"标识符": {"$regex": "test"}})
