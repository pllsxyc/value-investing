# DCF 估值计算器

部署在 `vi.starbugs.net` 的 Django 应用，用于做 DCF（自由现金流折现）估值。

## 功能

- **首页沪深300行情看板**（`/`）：展示沪深300（=爬虫 watchlist）成分股的现价与最近一次同步的涨跌幅、PE/PB；带名称/代码即时筛选框，点任意一行跳到计算器并预填该股。未登录也可浏览，仅提示注册/登录后可保存估值。
- **计算器**（`/calc/`）：三栏布局 · 收藏侧栏 · 输入参数 · 估值结果；顶栏常驻「开始计算」入口。
- 前端 JS 实时计算估值、年度现金流明细与敏感性分析（无需登录、无需提交）
- 用户注册 / 登录 / 退出
- 登录后可创建标签（消费、有色、科技……），并把估值结果按标签收藏
- **多选标签下拉框**：保存一条估值时可勾选多个标签，一条收藏可同时归入多个分类
- **侧栏「我的收藏 / 标签管理」两个标签页**：收藏页按标签折叠分组展示（未打标签归入「未分类」），标签管理页负责增删标签；两页各自独立滚动，不带动整页
- 点击某条收藏把当时全部参数回填表单并实时重算；带股票代码的收藏地址栏会变成可分享/刷新的 `/<用户名>/s/<代码>/`（仅本人可见）
- 收藏与标签均可删除（标签下还有收藏时禁止删除）
- **公司搜索/自动填充**：按名称或代码搜索已收录公司，自动带出代码、总股本、经营现金流参考值（只读复用爬虫库，详见下文）
- 金额单位统一为**万元**、总股本为**万股**（两者相约，每股价值仍为元）
- 每个财务参数旁有问号，悬停弹出专业说明
- **移动端响应式适配**：单域名自适应（无独立 m. 子域名），窄屏顶栏换行、宽表格横向滚动、首页行情表隐藏次要列。

## 技术栈

- Python 3.12 · Django 6.0 · MySQL/MariaDB（驱动 PyMySQL；缺省回退 SQLite，见环境变量）
- Django Template + 原生 CSS/JS（不引入前端构建链）
- 生产：Gunicorn + Nginx（HTTPS / HTTP2 / HTTP3）+ Let's Encrypt，systemd 管理

## 本地开发

```bash
# 1. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python manage.py migrate

# 4. （可选）创建管理员账号，用于访问 /admin/
python manage.py createsuperuser

# 5. 启动开发服务器
DJANGO_DEBUG=1 python manage.py runserver
```

打开 http://127.0.0.1:8000/ 即可。

> 本地必须设置 `DJANGO_DEBUG=1`：`DEBUG` 关闭时 `DJANGO_SECRET_KEY` 为必填，否则启动报错（见下）。开发模式下无需提供密钥。

改完代码后的自检：

```bash
DJANGO_DEBUG=1 python manage.py check
DJANGO_DEBUG=1 python manage.py test
```

## 环境变量

`SECRET_KEY`、`DEBUG`、`ALLOWED_HOSTS` 均从环境变量读取（`dcfsite/settings.py`）：

| 变量 | 说明 | 本地 | 生产 |
| --- | --- | --- | --- |
| `DJANGO_DEBUG` | 是否开启调试 | `1` | `0` |
| `DJANGO_SECRET_KEY` | 密钥，`DEBUG=0` 时必填 | 不需要 | 随机生成 |
| `DJANGO_ALLOWED_HOSTS` | 允许的 Host，逗号分隔 | 用默认即可 | `vi.starbugs.net,...` |
| `DCF_DB_ENGINE` | `mysql` 切到 MySQL；其余/不设则用 SQLite | 不设(SQLite) | `mysql` |
| `DCF_DB_NAME/USER/PASSWORD/HOST/PORT` | MySQL 连接（`DCF_DB_ENGINE=mysql` 时生效） | — | `dcf_data` / `dcf_user` / … / `127.0.0.1` / `3306` |
| `STOCK_DB_ENABLED` | 设 `1` 挂载只读 `stock` 连接做公司搜索（`DCF_DB_ENGINE=mysql` 时自动挂载） | 不设 | `1` |
| `STOCK_DB_NAME/USER/PASSWORD/HOST/PORT` | 只读复用爬虫库 `stock_data` 的连接 | — | `stock_data` / 只读账号 / … / `127.0.0.1` / `3306` |

数据库：默认 SQLite；设 `DCF_DB_ENGINE=mysql` 即切到 MySQL 库 `dcf_data`（与爬虫的 `stock_data` 相互独立）。生产已用 MySQL。

公司搜索/自动填充：计算器顶部的「搜索已收录公司」框会**只读**查询爬虫库 `stock_data`（`stock_basic`/`stock_share_capital`/`stock_financial_summary`），自动带出股票代码、总股本、经营现金流参考值（非真实 FCF）。该连接由 `STOCK_DB_*` 配置，仅用原生 SQL 读取、不迁移（见 `dcfsite/db_router.py`）；生产建议为其单独配一个只读 MySQL 账号。未配置或连接失败时，搜索框优雅降级提示「公司库未启用」，不影响计算器其余功能。

`DEBUG=False` 时自动启用生产安全项（强制 HTTPS、HSTS、安全 Cookie、`X-Frame-Options: DENY` 等）。生产环境变量写在 `/etc/dcfsite.env`（不纳入代码库），由 systemd 注入。

## 项目结构

```text
dcfsite/                 项目配置（settings / urls / wsgi）
calculator/
  models.py              DcfTag、DcfCalculation 模型（多对多 tags 关系）
  forms.py               表单与字段 help_text（参数问号说明）
  views.py               home() 沪深300行情、calculate_dcf() 计算逻辑、收藏/标签视图
  urls.py                路由
  templates/calculator/  页面与 _field.html 字段局部模板
  static/calculator/     style.css
db.sqlite3               旧 SQLite 数据（已迁移至 MySQL dcf_data，保留作历史备份/缺省回退）
```

路由：`/` 沪深300行情首页 · `/calc/` 计算器（可带 `?code=` 预填）· `/<用户名>/s/<代码>/` 收藏直达（仅本人）· `/favorites/` 收藏明细 · `/api/stock/search/` `/api/stock/autofill/` 公司搜索/自动填充 · `/login` `/logout` `/register` · `/admin/`

## DCF 计算逻辑

核心函数 `calculate_dcf(data)`（`calculator/views.py`）：

```text
企业价值 EV = Σ(FCFFt / (1 + WACC)^t) + 终值 / (1 + WACC)^n
终值        = FCFn × (1 + g) / (WACC - g)          # Gordon 永续增长
股权价值    = EV − 净有息债务 + 非经营性资产
每股价值    = 股权价值 / 总股本
```

表单校验：永续增长率 < 折现率；预测年数 ≥ 1；总股本 > 0。

## 部署（生产）

```bash
cd /var/www/value-investing                      # ← 生产目录就是这里（gunicorn 的 WorkingDirectory）
git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput   # ⚠️ 改过 CSS/JS/模板静态务必跑，否则线上还是旧样式
.venv/bin/python manage.py check --deploy        # 部署前自检
systemctl restart dcfsite.service                # Gunicorn，监听 127.0.0.1:8000
```

- Gunicorn 由 systemd 管理：`/etc/systemd/system/dcfsite.service`，`WorkingDirectory=/var/www/value-investing`。
- Nginx 站点配置：`/etc/nginx/conf.d/vi.starbugs.net.conf`（HTTPS 反代到 `127.0.0.1:8000`）。
  **`/static/` 的 alias 必须指向 `/var/www/value-investing/staticfiles/`**（即 `STATIC_ROOT`）——务必与上面的部署目录一致，否则应用渲染新页面、Nginx 却发旧 CSS，排版会乱。
- 改 Nginx 后：`nginx -t && systemctl reload nginx`（静态文件变更不需要重启 gunicorn）。
- 看日志：`journalctl -u dcfsite.service -f`
- ⚠️ 历史遗留目录 `/var/www/vi.starbugs.net` 是旧拷贝，已不再由 gunicorn/nginx-static 使用，**但仍是 Let's Encrypt 的 webroot**（`certbot` 的 `webroot_path` 指向它），不要删除。

## 注意事项

- 用户与收藏数据存 MySQL 库 `dcf_data`；备份用 `mysqldump dcf_data > dcf_data.sql`，并一并备份 `/etc/dcfsite.env`。
- 回滚到 SQLite：删除/注释 `/etc/dcfsite.env` 里的 `DCF_DB_*` 后重启服务即可（`db.sqlite3` 原样保留）。
- 迁移历史：原 SQLite 数据已通过 `dumpdata`→`migrate`→`loaddata` 迁入 MySQL。
- `staticfiles/` 是 `collectstatic` 生成目录，非源文件。
- 轮换密钥：更新 `/etc/dcfsite.env` 后重启服务（会使现有登录会话失效）。
