from datetime import date

import akshare as ak


def is_trading_day(target_date=None):
    target_date = target_date or date.today()
    if target_date.weekday() >= 5:
        return False
    try:
        calendar = ak.tool_trade_date_hist_sina()
        dates = set(calendar["trade_date"].astype(str).tolist())
        return target_date.isoformat() in dates
    except Exception:
        return True
