CREATE DATABASE IF NOT EXISTS stock_data DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE stock_data;

CREATE TABLE IF NOT EXISTS stock_watchlist (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    market VARCHAR(10),
    stock_name VARCHAR(100),
    enabled TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_code (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_basic (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    market VARCHAR(20),
    stock_name VARCHAR(100),
    company_name VARCHAR(200),
    industry VARCHAR(100),
    listing_date DATE,
    website VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(100),
    registered_address TEXT,
    office_address TEXT,
    main_business TEXT,
    business_scope TEXT,
    company_profile TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_code (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_daily_quote (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    close_price DECIMAL(12,4),
    market_cap DECIMAL(20,4),
    circulating_market_cap DECIMAL(20,4),
    pe_ttm DECIMAL(12,4),
    pe_static DECIMAL(12,4),
    pb DECIMAL(12,4),
    ps DECIMAL(12,4),
    pcf DECIMAL(12,4),
    dividend_yield DECIMAL(12,4),
    high_52w DECIMAL(12,4),
    low_52w DECIMAL(12,4),
    market_cap_52w_high DECIMAL(20,4),
    market_cap_52w_low DECIMAL(20,4),
    total_share DECIMAL(20,4),
    float_share DECIMAL(20,4),
    source VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (stock_code, trade_date),
    KEY idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_share_capital (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    change_date DATE NOT NULL,
    announcement_date DATE,
    change_reason VARCHAR(100),
    total_share DECIMAL(20,4),
    circulated_share DECIMAL(20,4),
    restricted_share DECIMAL(20,4),
    a_share DECIMAL(20,4),
    source VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_change_date (stock_code, change_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_top_holder (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    report_date DATE NOT NULL,
    announcement_date DATE,
    rank_no INT,
    holder_name VARCHAR(255),
    hold_amount DECIMAL(20,4),
    hold_ratio DECIMAL(10,4),
    share_type VARCHAR(100),
    holder_total_count BIGINT,
    avg_hold_amount DECIMAL(20,4),
    source VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_holder (stock_code, report_date, rank_no, holder_name),
    KEY idx_stock_report (stock_code, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_float_holder (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    report_date DATE NOT NULL,
    announcement_date DATE,
    rank_no INT,
    holder_name VARCHAR(255),
    hold_amount DECIMAL(20,4),
    hold_ratio DECIMAL(10,4),
    share_type VARCHAR(100),
    source VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_float_holder (stock_code, report_date, rank_no, holder_name),
    KEY idx_stock_report (stock_code, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_financial_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    report_date DATE NOT NULL,
    revenue DECIMAL(20,4),
    net_profit_parent DECIMAL(20,4),
    net_profit_deducted DECIMAL(20,4),
    total_assets DECIMAL(20,4),
    total_liability DECIMAL(20,4),
    net_assets DECIMAL(20,4),
    operating_cash_flow DECIMAL(20,4),
    eps DECIMAL(12,4),
    nav_per_share DECIMAL(12,4),
    cash_flow_per_share DECIMAL(12,4),
    roe DECIMAL(12,4),
    debt_ratio DECIMAL(12,4),
    source VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_report (stock_code, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_dividend (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    report_period VARCHAR(50),
    dividend_type VARCHAR(50),
    announcement_date DATE,
    record_date DATE,
    ex_dividend_date DATE,
    payment_date DATE,
    bonus_share_ratio DECIMAL(12,4),
    transfer_ratio DECIMAL(12,4),
    cash_dividend_ratio DECIMAL(12,4),
    dividend_desc VARCHAR(255),
    source VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_dividend (stock_code, announcement_date, report_period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS crawler_job_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    job_name VARCHAR(100),
    stock_code VARCHAR(20),
    run_date DATE,
    status VARCHAR(20),
    message TEXT,
    started_at DATETIME,
    finished_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_run_date (run_date),
    KEY idx_stock_code (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO stock_watchlist(stock_code, market, stock_name)
VALUES ('600900', 'SH', '长江电力')
ON DUPLICATE KEY UPDATE market=VALUES(market), stock_name=VALUES(stock_name), enabled=1;
