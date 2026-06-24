# Stock Crawler

基于 [akshare](https://akshare.akfamily.xyz/) 的 A 股数据爬虫，把公司资料 / 估值 / 股本 / 股东 / 财务 / 分红抓进独立的 **MySQL** 库 `stock_data`。与同仓库的 Django 估值站（根目录 `dcfsite`）相互独立，不共用数据库。

## 架构

```
stock_crawler/
├── config.py              读取 .env（MySQL 连接 + 限速 + 是否跳过非交易日）
├── db.py                  连接管理 / upsert 辅助 / job log
│                          - session(): 一次抓取共用一条连接（thread-local）
│                          - get_connection(): 有 session 则复用，否则临时新建
├── run_daily.py           入口：遍历自选股，逐只抓取
├── services/
│   ├── stock_service.py   各类数据的 upsert（ON DUPLICATE KEY UPDATE）
│   └── trading_calendar.py 是否交易日
├── sources/               每个文件对应一个 akshare 数据源
│   ├── company.py         公司资料   stock_profile_cninfo
│   ├── capital.py         股本结构   stock_share_change_cninfo
│   ├── quote.py           估值指标   stock_zh_valuation_baidu（含 52 周市值高/低）
│   ├── holders.py         十大/流通股东 stock_main_stock_holder / stock_circulate_stock_holder
│   ├── financial.py       财务摘要   stock_financial_abstract
│   └── dividend.py        分红送转   stock_dividend_cninfo
└── sql/schema.sql         建库 + 9 张表 + 样本自选股(600900)
```

数据源各自独立：`run_stock` 对 7 类数据逐一抓取，**单类失败只跳过那一类，其余照常入库**（见下方「抓取状态」）。

## 安装

```bash
cd /var/www/value-investing
.venv/bin/pip install -r requirements.txt
```

> ⚠️ 本机 pip 默认源是腾讯云内网镜像 `mirrors.tencentyun.com`，在非腾讯云环境连不上。
> 此时改用公共源：`.venv/bin/pip install -i https://pypi.org/simple -r requirements.txt`

## MySQL（本机用 MariaDB，协议兼容）

```bash
# 安装并启动
apt-get install -y mariadb-server mariadb-client
service mariadb start

# 建库 / 建表 / 样本自选股
mariadb < stock_crawler/sql/schema.sql

# 建应用账号（示例密码，生产请改强密码）
mariadb -e "CREATE USER IF NOT EXISTS 'stock_user'@'127.0.0.1' IDENTIFIED BY 'Stock_pass_2026!';
            GRANT ALL PRIVILEGES ON stock_data.* TO 'stock_user'@'127.0.0.1'; FLUSH PRIVILEGES;"

# 配置连接
cp stock_crawler/.env.example stock_crawler/.env   # 然后填入上面的账号密码
```

## 运行

```bash
cd /var/www/value-investing
.venv/bin/python -m stock_crawler.run_daily
```

结尾打印汇总：`done: N stocks — X ok, Y partial, Z failed`。

### Cron（交易日 15:30）

```cron
30 15 * * 1-5 cd /var/www/value-investing && /var/www/value-investing/.venv/bin/python -m stock_crawler.run_daily >> /var/www/value-investing/stock_crawler/logs/daily.log 2>&1
```

## 管理自选股（watchlist）

`run_daily` 每次只抓 `stock_watchlist` 里 `enabled=1` 的股票。**真正必填的只有 `stock_code`**（6 位纯数字，不带 sh/sz 前缀）；`market`/`stock_name` 仅作备注，真实信息抓取时写入 `stock_basic`。

```sql
-- 增加（重复插入或重新启用）
INSERT INTO stock_watchlist(stock_code, market, stock_name) VALUES ('600519','SH','贵州茅台')
ON DUPLICATE KEY UPDATE market=VALUES(market), stock_name=VALUES(stock_name), enabled=1;

-- 暂停（保留历史数据）
UPDATE stock_watchlist SET enabled=0 WHERE stock_code='600519';
```

### 批量导入指数成分股（例：沪深300）

```python
import akshare as ak
from stock_crawler.db import get_connection
df = ak.index_stock_cons_csindex(symbol="000300")        # 300 只成分券
rows = [(str(c).zfill(6), "SH" if str(c)[0]=="6" else "SZ", n)
        for c, n in zip(df["成分券代码"], df["成分券名称"])]
sql = """INSERT INTO stock_watchlist(stock_code,market,stock_name) VALUES (%s,%s,%s)
         ON DUPLICATE KEY UPDATE market=VALUES(market),stock_name=VALUES(stock_name),enabled=1"""
with get_connection() as conn, conn.cursor() as cur:
    cur.executemany(sql, rows)
```

## 抓取状态（crawler_job_log）

每只股票每次跑写一条 `crawler_job_log`：

| status | 含义 |
| --- | --- |
| `success` | 7 类数据全部入库 |
| `partial` | 部分数据源失败；`message` 列出失败类目（如 `dividends: ...`），其余已入库 |
| `failed`  | 整只失败（一般是连库失败等） |
| `skipped` | 非交易日跳过（`SKIP_NON_TRADING_DAY=true` 时） |

## 数据时效性

判断时效性有两个维度，都可查：

| 维度 | 含义 | 字段 |
| --- | --- | --- |
| **数据时点** | 数据「截止到哪天」 | `trade_date`（行情）、`report_date`（财务/股东）、`announcement_date`（分红） |
| **最后抓取** | 我们「最近一次更新/核对」的时间 | 各表 `updated_at`（每次 upsert 强制刷新，数据没变也刷新） |

```sql
-- 单只股票各类数据的时效性
SELECT '行情' 类型, MAX(trade_date) 数据时点, MAX(updated_at) 最后抓取 FROM stock_daily_quote WHERE stock_code='600519'
UNION ALL SELECT '财务', MAX(report_date), MAX(updated_at) FROM stock_financial_summary WHERE stock_code='600519'
UNION ALL SELECT '十大股东', MAX(report_date), MAX(updated_at) FROM stock_top_holder WHERE stock_code='600519';
```

## 已知边界

- akshare 接口偶发返回空/非 JSON（`Expecting value: line 1 column 1`）或网络超时——属上游问题，重跑多半恢复。
- 少数次新股/科创板（如中芯国际 688981）的 `stock_dividend_cninfo` / 股本接口因列结构不同会稳定报 KeyError；得益于按源隔离，这类股票其余数据仍正常入库，只缺报错类目。
