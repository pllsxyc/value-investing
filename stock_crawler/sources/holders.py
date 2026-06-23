import akshare as ak


def fetch_top_holders(stock_code):
    df = ak.stock_main_stock_holder(stock=stock_code)
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "stock_code": stock_code,
            "report_date": row.get("截至日期"),
            "announcement_date": row.get("公告日期"),
            "rank_no": row.get("编号"),
            "holder_name": row.get("股东名称"),
            "hold_amount": row.get("持股数量"),
            "hold_ratio": row.get("持股比例"),
            "share_type": row.get("股本性质"),
            "holder_total_count": row.get("股东总数"),
            "avg_hold_amount": row.get("平均持股数"),
        })
    return rows


def fetch_float_holders(stock_code):
    df = ak.stock_circulate_stock_holder(symbol=stock_code)
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "stock_code": stock_code,
            "report_date": row.get("截止日期"),
            "announcement_date": row.get("公告日期"),
            "rank_no": row.get("编号"),
            "holder_name": row.get("股东名称"),
            "hold_amount": row.get("持股数量"),
            "hold_ratio": row.get("占流通股比例"),
            "share_type": row.get("股本性质"),
        })
    return rows
