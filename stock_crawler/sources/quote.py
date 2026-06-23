from datetime import date

import akshare as ak


VALUATION_INDICATORS = {
    "market_cap": "总市值",
    "pe_ttm": "市盈率(TTM)",
    "pe_static": "市盈率(静)",
    "pb": "市净率",
    "pcf": "市现率",
}


def fetch_daily_quote(stock_code, trade_date=None):
    trade_date = trade_date or date.today()
    result = {
        "stock_code": stock_code,
        "trade_date": trade_date,
        "market_cap": None,
        "pe_ttm": None,
        "pe_static": None,
        "pb": None,
        "pcf": None,
        "total_share": None,
        "float_share": None,
        "source": "baidu/akshare",
    }
    for field, indicator in VALUATION_INDICATORS.items():
        df = ak.stock_zh_valuation_baidu(symbol=stock_code, indicator=indicator, period="近一年")
        df = df.dropna()
        if df.empty:
            continue
        latest = df.iloc[-1]
        result[field] = latest.get("value")
        if field == "market_cap":
            result["market_cap_52w_high"] = df["value"].max()
            result["market_cap_52w_low"] = df["value"].min()
    return result
