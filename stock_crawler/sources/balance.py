import akshare as ak


# 东方财富资产负债表（按报告期）列名 → 本地字段。全部为「元」。
# 取「有息负债」与「非经营性资产」估算所需的明细科目，原始值入库，口径换算放到消费端。
BALANCE_MAPPING = {
    "monetary_funds": "MONETARYFUNDS",                  # 货币资金
    "trade_finasset": "TRADE_FINASSET",                 # 交易性金融资产
    "other_equity_invest": "OTHER_EQUITY_INVEST",       # 其他权益工具投资
    "other_noncurrent_finasset": "OTHER_NONCURRENT_FINASSET",  # 其他非流动金融资产
    "short_loan": "SHORT_LOAN",                         # 短期借款
    "short_bond_payable": "SHORT_BOND_PAYABLE",         # 短期应付债券
    "noncurrent_liab_1year": "NONCURRENT_LIAB_1YEAR",   # 一年内到期的非流动负债
    "long_loan": "LONG_LOAN",                           # 长期借款
    "bond_payable": "BOND_PAYABLE",                     # 应付债券
}


def _market_symbol(stock_code):
    """东方财富接口需要带交易所前缀，如 SH600900 / SZ000001 / BJ831010。"""
    code = str(stock_code)
    if code.startswith("6"):
        return f"SH{code}"
    if code.startswith(("0", "3")):
        return f"SZ{code}"
    if code.startswith(("4", "8", "9")):
        return f"BJ{code}"
    return f"SH{code}"


def fetch_balance_sheet(stock_code):
    """抓取各报告期资产负债表明细。NaN 由 db.clean_value 统一转 None。"""
    df = ak.stock_balance_sheet_by_report_em(symbol=_market_symbol(stock_code))
    if df is None or df.empty or "REPORT_DATE" not in df.columns:
        return []
    rows = []
    for _, record in df.iterrows():
        report_date = str(record.get("REPORT_DATE") or "")[:10]
        if not report_date:
            continue
        item = {"stock_code": stock_code, "report_date": report_date}
        for target_name, source_name in BALANCE_MAPPING.items():
            item[target_name] = record.get(source_name)
        rows.append(item)
    return rows
