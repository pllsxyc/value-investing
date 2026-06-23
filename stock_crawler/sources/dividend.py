import akshare as ak


def fetch_dividends(stock_code):
    df = ak.stock_dividend_cninfo(symbol=stock_code)
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "stock_code": stock_code,
            "report_period": row.get("报告时间"),
            "dividend_type": row.get("分红类型"),
            "announcement_date": row.get("实施方案公告日期"),
            "record_date": row.get("股权登记日"),
            "ex_dividend_date": row.get("除权日"),
            "payment_date": row.get("派息日"),
            "bonus_share_ratio": row.get("送股比例"),
            "transfer_ratio": row.get("转增比例"),
            "cash_dividend_ratio": row.get("派息比例"),
            "dividend_desc": row.get("实施方案分红说明"),
        })
    return rows
