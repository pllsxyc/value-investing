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
    """Crawl all data sources for one stock. Each source is isolated: a single
    source failing only skips that category, the rest still gets stored.
    Returns a list of per-source error strings (empty means fully successful)."""
    started_at = datetime.now()
    errors = []

    def step(label, fn):
        try:
            return fn()
        except Exception as exc:
            errors.append(f"{label}: {exc}")
            return None

    with session():
        step("company", lambda: upsert_company(fetch_company_profile(stock_code)))

        capital = step("capital", lambda: fetch_latest_share_capital(stock_code))
        if capital is not None:
            step("capital", lambda: upsert_share_capital(capital))

        def do_quote():
            quote = fetch_daily_quote(stock_code, run_date)
            if capital:
                quote["total_share"] = capital.get("total_share")
                quote["float_share"] = capital.get("circulated_share")
            upsert_daily_quote(quote)
        step("quote", do_quote)

        step("top_holders", lambda: upsert_top_holders(fetch_top_holders(stock_code)))
        step("float_holders", lambda: upsert_float_holders(fetch_float_holders(stock_code)))
        step("financial", lambda: upsert_financial_summary(fetch_financial_summary(stock_code)))
        step("dividends", lambda: upsert_dividends(fetch_dividends(stock_code)))

    status = "partial" if errors else "success"
    log_job("daily_stock_crawler", stock_code, run_date, status, "; ".join(errors) or "ok", started_at)
    return errors


def main():
    run_date = date.today()
    if SKIP_NON_TRADING_DAY and not is_trading_day(run_date):
        log_job("daily_stock_crawler", None, run_date, "skipped", "non trading day", datetime.now())
        return
    stocks = get_enabled_stocks()
    full = partial = failed = 0
    for item in stocks:
        try:
            errors = run_stock(item["stock_code"], run_date)
            if errors:
                partial += 1
                print(f"[{item['stock_code']}] partial: {'; '.join(errors)}")
            else:
                full += 1
        except Exception as exc:
            failed += 1
            print(f"[{item['stock_code']}] failed: {exc}")
        time.sleep(CRAWLER_SLEEP_SECONDS)
    print(f"done: {len(stocks)} stocks — {full} ok, {partial} partial, {failed} failed")


if __name__ == "__main__":
    main()
