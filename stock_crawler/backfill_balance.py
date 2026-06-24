"""一次性回填全部 watchlist 的资产负债表（balance）。幂等，可重复跑。

用法：.venv/bin/python -m stock_crawler.backfill_balance
"""
import time

from stock_crawler.config import CRAWLER_SLEEP_SECONDS
from stock_crawler.db import session
from stock_crawler.services.stock_service import get_enabled_stocks, upsert_balance_sheet
from stock_crawler.sources.balance import fetch_balance_sheet


def main():
    stocks = get_enabled_stocks()
    ok = failed = 0
    for item in stocks:
        code = item["stock_code"]
        try:
            with session():
                rows = fetch_balance_sheet(code)
                upsert_balance_sheet(rows)
            ok += 1
            print(f"[{code}] ok: {len(rows)} rows", flush=True)
        except Exception as exc:
            failed += 1
            print(f"[{code}] failed: {exc!r}", flush=True)
        time.sleep(CRAWLER_SLEEP_SECONDS)
    print(f"backfill done: {len(stocks)} stocks — {ok} ok, {failed} failed", flush=True)


if __name__ == "__main__":
    main()
