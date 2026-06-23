import time
from datetime import date, datetime

from stock_crawler.config import CRAWLER_SLEEP_SECONDS, SKIP_NON_TRADING_DAY
from stock_crawler.db import log_job, session
from stock_crawler.services.stock_service import (
    get_enabled_stocks,
    upsert_company,
    upsert_daily_quote,
    upsert_dividends,
    upsert_financial_summary,
    upsert_float_holders,
    upsert_share_capital,
    upsert_top_holders,
)
from stock_crawler.services.trading_calendar import is_trading_day
from stock_crawler.sources.capital import fetch_latest_share_capital
from stock_crawler.sources.company import fetch_company_profile
from stock_crawler.sources.dividend import fetch_dividends
from stock_crawler.sources.financial import fetch_financial_summary
from stock_crawler.sources.holders import fetch_float_holders, fetch_top_holders
from stock_crawler.sources.quote import fetch_daily_quote


def run_stock(stock_code, run_date):
    started_at = datetime.now()
    try:
        with session():
            upsert_company(fetch_company_profile(stock_code))
            capital = fetch_latest_share_capital(stock_code)
            upsert_share_capital(capital)
            quote = fetch_daily_quote(stock_code, run_date)
            if capital:
                quote["total_share"] = capital.get("total_share")
                quote["float_share"] = capital.get("circulated_share")
            upsert_daily_quote(quote)
            upsert_top_holders(fetch_top_holders(stock_code))
            upsert_float_holders(fetch_float_holders(stock_code))
            upsert_financial_summary(fetch_financial_summary(stock_code))
            upsert_dividends(fetch_dividends(stock_code))
        log_job("daily_stock_crawler", stock_code, run_date, "success", "ok", started_at)
    except Exception as exc:
        log_job("daily_stock_crawler", stock_code, run_date, "failed", str(exc), started_at)
        raise


def main():
    run_date = date.today()
    if SKIP_NON_TRADING_DAY and not is_trading_day(run_date):
        log_job("daily_stock_crawler", None, run_date, "skipped", "non trading day", datetime.now())
        return
    stocks = get_enabled_stocks()
    failed = 0
    for item in stocks:
        try:
            run_stock(item["stock_code"], run_date)
        except Exception as exc:
            failed += 1
            print(f"[{item['stock_code']}] failed: {exc}")
        time.sleep(CRAWLER_SLEEP_SECONDS)
    print(f"done: {len(stocks)} stocks, {failed} failed")


if __name__ == "__main__":
    main()
