import akshare as ak


FINANCIAL_MAPPING = {
    "营业总收入": "revenue",
    "归母净利润": "net_profit_parent",
    "扣非净利润": "net_profit_deducted",
    "资产总计": "total_assets",
    "负债合计": "total_liability",
    "股东权益合计(净资产)": "net_assets",
    "经营现金流量净额": "operating_cash_flow",
    "基本每股收益": "eps",
    "每股净资产": "nav_per_share",
    "每股现金流": "cash_flow_per_share",
    "净资产收益率(ROE)": "roe",
    "资产负债率": "debt_ratio",
}


def fetch_financial_summary(stock_code):
    df = ak.stock_financial_abstract(symbol=stock_code)
    period_cols = [col for col in df.columns if str(col).isdigit()]
    rows = []
    for period in period_cols:
        item = {
            "stock_code": stock_code,
            "report_date": f"{str(period)[:4]}-{str(period)[4:6]}-{str(period)[6:8]}",
            "revenue": None,
            "net_profit_parent": None,
            "net_profit_deducted": None,
            "total_assets": None,
            "total_liability": None,
            "net_assets": None,
            "operating_cash_flow": None,
            "eps": None,
            "nav_per_share": None,
            "cash_flow_per_share": None,
            "roe": None,
            "debt_ratio": None,
        }
        for source_name, target_name in FINANCIAL_MAPPING.items():
            matched = df[df["指标"] == source_name]
            if not matched.empty:
                item[target_name] = matched.iloc[0].get(period)
        rows.append(item)
    return rows
