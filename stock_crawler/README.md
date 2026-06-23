# Stock Crawler

## Install

```bash
cd /var/www/value-investing
.venv/bin/pip install -r requirements.txt
```

## MySQL

```bash
mysql -u root -p < stock_crawler/sql/schema.sql
cp stock_crawler/.env.example stock_crawler/.env
```

Edit `stock_crawler/.env` with MySQL credentials.

## Run

```bash
cd /var/www/value-investing
.venv/bin/python -m stock_crawler.run_daily
```

## Cron

```cron
30 15 * * 1-5 cd /var/www/value-investing && /var/www/value-investing/.venv/bin/python -m stock_crawler.run_daily >> /var/www/value-investing/stock_crawler/logs/daily.log 2>&1
```
