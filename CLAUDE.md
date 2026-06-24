# CLAUDE.md

给在本仓库工作的 Claude 的导览。仓库包含**两个相互独立的子系统**：

1. **DCF 估值站**（根目录 + `dcfsite/` + `calculator/`）——线上 `vi.starbugs.net` 的 Django 应用，数据存 **SQLite**(`db.sqlite3`)。详见 [README.md](README.md)。
2. **股票爬虫**（`stock_crawler/`）——基于 akshare 的 A 股数据爬虫，数据存独立的 **MySQL/MariaDB** 库 `stock_data`。详见 [stock_crawler/README.md](stock_crawler/README.md)。

两者不共用数据库、不互相 import。改其中一个一般不影响另一个。

## 环境

- 解释器固定用仓库内的 **`.venv`**：`/var/www/value-investing/.venv/bin/python`（系统无全局 venv 激活）。
- ⚠️ **pip 默认源是腾讯云内网镜像 `mirrors.tencentyun.com`，非腾讯云环境连不上**。装包加 `-i https://pypi.org/simple`。
- 运行 Django 的 `manage.py` 命令本地必须带 `DJANGO_DEBUG=1`，否则 `DJANGO_SECRET_KEY` 变必填、启动报错。

## DCF 估值站（Django）

- 设置模块 `dcfsite.settings`；核心计算在 `calculator/views.py` 的 `calculate_dcf()`；模型 `DcfTag` / `DcfCalculation`（多对多 tags）。
- 估值在前端 JS 实时算，不提交后端；后端负责账号、标签、收藏。
- 金额单位**万元**、总股本**万股**。
- 自检：`DJANGO_DEBUG=1 .venv/bin/python manage.py check && DJANGO_DEBUG=1 .venv/bin/python manage.py test`
- 生产部署、环境变量、Nginx/systemd 细节都在 README.md，勿在代码里硬编码密钥/Host。
- 待办见 [TODO.md](TODO.md)（按股票代码自动带出公司名/总股本——可考虑复用 stock_crawler 的数据）。

## 股票爬虫（stock_crawler）

- 入口：`.venv/bin/python -m stock_crawler.run_daily`，遍历 `stock_watchlist` 中 `enabled=1` 的股票。
- 连接通过 `stock_crawler/.env` 配置（不入库，已在 .gitignore）；schema 在 `sql/schema.sql`。
- **分层**：`sources/*`（抓 akshare，返回 dict/list）→ `services/stock_service.py`（upsert）→ `run_daily`（调度）。加新数据源就照这三层加。
- **连接复用**：`db.session()` 让一次抓取内所有 `execute_*` 共用一条连接；`get_connection()` 在有 session 时复用、否则临时新建。`log_job` 故意走独立短连接，避免被回滚的事务牵连。
- **按数据源隔离**：`run_stock` 里每类数据各包 try/except，单类失败只跳过该类、状态记 `partial`，其余照常入库。不要把多个源重新合并进一个 try。
- **upsert 一律 `ON DUPLICATE KEY UPDATE` 且刷新 `updated_at=CURRENT_TIMESTAMP()`**（幂等 + 反映最近抓取时间）。加新表/新列时沿用这个约定，并同步改 `sql/schema.sql` 与线上 `ALTER TABLE`。
- **时效性两维度**：数据时点（`trade_date`/`report_date`）vs 最后抓取（`updated_at`）。

## 改动后的验证习惯

- 改 Django：跑 `manage.py check` + `test`。
- 改爬虫：`mariadb -D stock_data` 直接查行数与 `crawler_job_log` 的 status/message 确认落库；akshare 接口偶发失败是上游问题，重跑确认。
- 涉及 git 提交时：只在用户明确要求时提交；当前默认分支 `main`。
