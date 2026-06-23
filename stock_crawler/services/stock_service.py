from stock_crawler.db import execute_many, execute_one, fetch_all


def get_enabled_stocks():
    return fetch_all("SELECT stock_code FROM stock_watchlist WHERE enabled = 1 ORDER BY stock_code")


def upsert_company(profile):
    if not profile:
        return
    execute_one(
        """
        INSERT INTO stock_basic
        (stock_code, market, stock_name, company_name, industry, listing_date, website, email, phone,
         registered_address, office_address, main_business, business_scope, company_profile)
        VALUES (%(stock_code)s, %(market)s, %(stock_name)s, %(company_name)s, %(industry)s, %(listing_date)s,
                %(website)s, %(email)s, %(phone)s, %(registered_address)s, %(office_address)s,
                %(main_business)s, %(business_scope)s, %(company_profile)s)
        ON DUPLICATE KEY UPDATE
            market=VALUES(market), stock_name=VALUES(stock_name), company_name=VALUES(company_name),
            industry=VALUES(industry), listing_date=VALUES(listing_date), website=VALUES(website),
            email=VALUES(email), phone=VALUES(phone), registered_address=VALUES(registered_address),
            office_address=VALUES(office_address), main_business=VALUES(main_business),
            business_scope=VALUES(business_scope), company_profile=VALUES(company_profile)
        """,
        profile,
    )


def upsert_share_capital(row):
    if not row:
        return
    execute_one(
        """
        INSERT INTO stock_share_capital
        (stock_code, change_date, announcement_date, change_reason, total_share, circulated_share,
         restricted_share, a_share, source)
        VALUES (%(stock_code)s, %(change_date)s, %(announcement_date)s, %(change_reason)s, %(total_share)s,
                %(circulated_share)s, %(restricted_share)s, %(a_share)s, 'cninfo/akshare')
        ON DUPLICATE KEY UPDATE
            announcement_date=VALUES(announcement_date), change_reason=VALUES(change_reason),
            total_share=VALUES(total_share), circulated_share=VALUES(circulated_share),
            restricted_share=VALUES(restricted_share), a_share=VALUES(a_share), source=VALUES(source)
        """,
        row,
    )


def upsert_daily_quote(row):
    execute_one(
        """
        INSERT INTO stock_daily_quote
        (stock_code, trade_date, market_cap, pe_ttm, pe_static, pb, pcf, total_share, float_share, source)
        VALUES (%(stock_code)s, %(trade_date)s, %(market_cap)s, %(pe_ttm)s, %(pe_static)s, %(pb)s,
                %(pcf)s, %(total_share)s, %(float_share)s, %(source)s)
        ON DUPLICATE KEY UPDATE
            market_cap=VALUES(market_cap), pe_ttm=VALUES(pe_ttm), pe_static=VALUES(pe_static),
            pb=VALUES(pb), pcf=VALUES(pcf), total_share=VALUES(total_share),
            float_share=VALUES(float_share), source=VALUES(source)
        """,
        row,
    )


def upsert_top_holders(rows):
    execute_many(
        """
        INSERT INTO stock_top_holder
        (stock_code, report_date, announcement_date, rank_no, holder_name, hold_amount, hold_ratio,
         share_type, holder_total_count, avg_hold_amount, source)
        VALUES (%(stock_code)s, %(report_date)s, %(announcement_date)s, %(rank_no)s, %(holder_name)s,
                %(hold_amount)s, %(hold_ratio)s, %(share_type)s, %(holder_total_count)s,
                %(avg_hold_amount)s, 'sina/akshare')
        ON DUPLICATE KEY UPDATE
            announcement_date=VALUES(announcement_date), hold_amount=VALUES(hold_amount),
            hold_ratio=VALUES(hold_ratio), share_type=VALUES(share_type),
            holder_total_count=VALUES(holder_total_count), avg_hold_amount=VALUES(avg_hold_amount), source=VALUES(source)
        """,
        rows,
    )


def upsert_float_holders(rows):
    execute_many(
        """
        INSERT INTO stock_float_holder
        (stock_code, report_date, announcement_date, rank_no, holder_name, hold_amount, hold_ratio, share_type, source)
        VALUES (%(stock_code)s, %(report_date)s, %(announcement_date)s, %(rank_no)s, %(holder_name)s,
                %(hold_amount)s, %(hold_ratio)s, %(share_type)s, 'sina/akshare')
        ON DUPLICATE KEY UPDATE
            announcement_date=VALUES(announcement_date), hold_amount=VALUES(hold_amount),
            hold_ratio=VALUES(hold_ratio), share_type=VALUES(share_type), source=VALUES(source)
        """,
        rows,
    )


def upsert_financial_summary(rows):
    execute_many(
        """
        INSERT INTO stock_financial_summary
        (stock_code, report_date, revenue, net_profit_parent, net_profit_deducted, total_assets,
         total_liability, net_assets, operating_cash_flow, eps, nav_per_share, cash_flow_per_share,
         roe, debt_ratio, source)
        VALUES (%(stock_code)s, %(report_date)s, %(revenue)s, %(net_profit_parent)s, %(net_profit_deducted)s,
                %(total_assets)s, %(total_liability)s, %(net_assets)s, %(operating_cash_flow)s,
                %(eps)s, %(nav_per_share)s, %(cash_flow_per_share)s, %(roe)s, %(debt_ratio)s, 'akshare')
        ON DUPLICATE KEY UPDATE
            revenue=VALUES(revenue), net_profit_parent=VALUES(net_profit_parent),
            net_profit_deducted=VALUES(net_profit_deducted), total_assets=VALUES(total_assets),
            total_liability=VALUES(total_liability), net_assets=VALUES(net_assets),
            operating_cash_flow=VALUES(operating_cash_flow), eps=VALUES(eps),
            nav_per_share=VALUES(nav_per_share), cash_flow_per_share=VALUES(cash_flow_per_share),
            roe=VALUES(roe), debt_ratio=VALUES(debt_ratio), source=VALUES(source)
        """,
        rows,
    )


def upsert_dividends(rows):
    execute_many(
        """
        INSERT INTO stock_dividend
        (stock_code, report_period, dividend_type, announcement_date, record_date, ex_dividend_date,
         payment_date, bonus_share_ratio, transfer_ratio, cash_dividend_ratio, dividend_desc, source)
        VALUES (%(stock_code)s, %(report_period)s, %(dividend_type)s, %(announcement_date)s,
                %(record_date)s, %(ex_dividend_date)s, %(payment_date)s, %(bonus_share_ratio)s,
                %(transfer_ratio)s, %(cash_dividend_ratio)s, %(dividend_desc)s, 'cninfo/akshare')
        ON DUPLICATE KEY UPDATE
            dividend_type=VALUES(dividend_type), record_date=VALUES(record_date),
            ex_dividend_date=VALUES(ex_dividend_date), payment_date=VALUES(payment_date),
            bonus_share_ratio=VALUES(bonus_share_ratio), transfer_ratio=VALUES(transfer_ratio),
            cash_dividend_ratio=VALUES(cash_dividend_ratio), dividend_desc=VALUES(dividend_desc), source=VALUES(source)
        """,
        rows,
    )
