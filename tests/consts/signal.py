import pandas as pd

TDATE = pd.Timestamp("2021-05-17")

const_signal = {
    "选股": {
        "data": {
            "SYMBOL": ["600519", "601012"],
            "EXCHANGE": ["CNSESH", "CNSESH"],
            "TDATE": [TDATE, TDATE],
            "SCORE": [2.27445, 2.95099],
            "TCLOSE": [3.05000, 9.68000],
        },
        "idx": pd.Index([TDATE, TDATE]),
    },
    "择时": {
        "data": {
            "TDATE": [TDATE.strftime("%Y%m%d")],
            # 000300
            "tclose_000300": [5184.99000],
            "position_rate_000300": [1.00000],
            "position_rate_advice_000300": ["70-100%"],
            "market_trend_shape_000300": ["上升"],
            "operation_advice_000300": [8],
            "high_value_000300": [0],
            # 399001
            "tclose_399001": [14456.50000],
            "position_rate_399001": [0.00000],
            "position_rate_advice_399001": ["0-20%"],
            "market_trend_shape_399001": ["下降"],
            "operation_advice_399001": [1],
            "high_value_399001": [0],
            # 000001
            "tclose_000001": [3517.62000],
            "position_rate_000001": [0.30000],
            "position_rate_advice_000001": ["40-50%"],
            "market_trend_shape_000001": ["反弹"],
            "operation_advice_000001": [5],
            "high_value_000001": [0],
            # 000905
            "tclose_000905": [6578.14000],
            "position_rate_000905": [0.30000],
            "position_rate_advice_000905": ["40-50%"],
            "market_trend_shape_000905": ["反弹"],
            "operation_advice_000905": [5],
            "high_value_000905": [0],
            # 399006
            "tclose_399006": [3112.74000],
            "position_rate_399006": [1.00000],
            "position_rate_advice_399006": ["70-100%"],
            "market_trend_shape_399006": ["上升"],
            "operation_advice_399006": [8],
            "high_value_399006": [0],
        },
        "idx": pd.Index([TDATE]),
    },
    "交易": {
        "data": {
            "SYMBOL": ["601816", "600837", "002568"],
            "EXCHANGE": ["CNSESH", "CNSESH", "CNSESZ"],
            "TDATE": [TDATE, TDATE, TDATE],
            "SIGNAL": [0, -1, 1],
            "TCLOSE": [54.69, 2.75000, 135.00000],
            "REASON": ["('0',)", "('卖1', -68.0)", "('买2', 88.0)"],
        },
        "idx": pd.Index([TDATE, TDATE, TDATE]),
    },
    "风控": {
        "data": {
            "symbol": ["600298", "002054", "603386"],
            "exchange": ["CNSESH", "CNSESZ", "CNSESH"],
            "tdate": [TDATE, TDATE, TDATE],
            "identiy": [16, 16, 16],
            "exlpain": ["正常", "正常", "长期偿债能力严重不足"],
            "grade": ["正常", "低风险", "高风险"],
        },
        "idx": pd.Index([TDATE, TDATE, TDATE]),
    },
    "大类资产配置": {
        "data": {
            "SYMBOL": ["159920", "511010", "513100"],
            "EXCHANGE": ["CNSESZ", "CNSESH", "CNSESH"],
            "TDATE": [TDATE, TDATE, TDATE],
            "SHARE": [0.00000, 0.50000, 0.33000],
            "TCLOSE": [1.46300, 122.88700, 4.43900],
        },
        "idx": pd.Index([TDATE, TDATE, TDATE]),
    },
    "基金定投": {
        "data": {
            "SYMBOL": ["510500"],
            "EXCHANGE": ["CNSESH"],
            "TDATE": [TDATE],
            "SHARE": [1.00000],
            "TCLOSE": [1.46300],
        },
        "idx": pd.Index([TDATE]),
    },
    "风控包": [
        {
            "data": {
                "symbol": ["600298", "002054", "603386"],
                "exchange": ["CNSESH", "CNSESZ", "CNSESH"],
                "tdate": [TDATE, TDATE, TDATE],
                "identiy": [16, 16, 16],
                "exlpain": ["正常", "正常", "长期偿债能力严重不足"],
                "grade": ["正常", "低风险", "高风险"],
            },
            "idx": pd.Index([TDATE, TDATE, TDATE]),
        },
        {
            "data": {
                "symbol": ["600000", "600070", "600077"],
                "exchange": ["CNSESH", "CNSESH", "CNSESH"],
                "tdate": [TDATE, TDATE, TDATE],
                "identiy": [20, 20, 16],
                "exlpain": ["正常", "经营现金流净额连续多个周期小于净利润", "经营现金流净额连续多个周期远远小于净利润"],
                "grade": ["正常", "低风险", "高风险"],
            },
            "idx": pd.Index([TDATE, TDATE, TDATE]),
        },
    ],
}
