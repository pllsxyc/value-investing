import akshare as ak


def fetch_latest_share_capital(stock_code):
    df = ak.stock_share_change_cninfo(symbol=stock_code)
    if df.empty:
        return None
    df = df.sort_values("变动日期")
    row = df.iloc[-1]
    return {
        "stock_code": stock_code,
        "change_date": row.get("变动日期"),
        "announcement_date": row.get("公告日期"),
        "change_reason": row.get("变动原因"),
        "total_share": row.get("总股本"),
        "circulated_share": row.get("已流通股份"),
        "restricted_share": row.get("流通受限股份"),
        "a_share": row.get("人民币普通股"),
    }
