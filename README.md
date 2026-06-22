# DCF 估值计算器

部署在 `vi.starbugs.net` 的 Django 应用，用于做 DCF（自由现金流折现）估值。

## 功能

- 三栏布局：标签与收藏侧栏 · 输入参数 · 估值结果
- 前端 JS 实时计算估值、年度现金流明细与敏感性分析（无需登录、无需提交）
- 用户注册 / 登录 / 退出
- 登录后可创建标签（消费、有色、科技……），并把估值结果按标签收藏
- **多选标签下拉框**：保存一条估值时可勾选多个标签，一条收藏可同时归入多个分类
- **左侧标签与收藏合并为一棵树**：顶部「添加标签」，每个标签为可折叠分组，保存的收藏折叠展示在对应标签下；未打标签的归入「未分类」
- 点击某条收藏可把当时的全部参数回填到表单并实时重算
- 收藏与标签均可删除（标签下还有收藏时禁止删除）
- 金额单位统一为**万元**、总股本为**万股**（两者相约，每股价值仍为元）
- 每个财务参数旁有问号，悬停弹出专业说明

> 计划中的功能见 [TODO.md](TODO.md)（如按股票代码自动带出公司名称与总股本）。

## 技术栈

- Python 3.12 · Django 6.0 · SQLite
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

`DEBUG=False` 时自动启用生产安全项（强制 HTTPS、HSTS、安全 Cookie、`X-Frame-Options: DENY` 等）。生产环境变量写在 `/etc/dcfsite.env`（不纳入代码库），由 systemd 注入。

## 项目结构

```text
dcfsite/                 项目配置（settings / urls / wsgi）
calculator/
  models.py              DcfTag、DcfCalculation 模型（多对多 tags 关系）
  forms.py               表单与字段 help_text（参数问号说明）
  views.py               calculate_dcf() 计算逻辑、收藏/标签视图
  urls.py                路由
  templates/calculator/  页面与 _field.html 字段局部模板
  static/calculator/     style.css
db.sqlite3               用户与收藏数据（备份时必须包含）
```

路由：`/` 计算器 · `/favorites/` 收藏明细 · `/login` `/logout` `/register` · `/admin/`

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
cd /var/www/vi.starbugs.net
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy        # 部署前自检
systemctl restart dcfsite.service                # Gunicorn，监听 127.0.0.1:8000
```

- Gunicorn 由 systemd 管理：`/etc/systemd/system/dcfsite.service`
- Nginx 站点配置：`/etc/nginx/conf.d/vi.starbugs.net.conf`（HTTPS 反代到 `127.0.0.1:8000`，静态文件直出 `staticfiles/`）
- 改 Nginx 后：`nginx -t && systemctl reload nginx`
- 看日志：`journalctl -u dcfsite.service -f`

## 注意事项

- SQLite 适合小规模；用户量增长后建议迁移 PostgreSQL。
- 备份须包含 `db.sqlite3` 与 `/etc/dcfsite.env`。
- `staticfiles/` 是 `collectstatic` 生成目录，非源文件。
- 轮换密钥：更新 `/etc/dcfsite.env` 后重启服务（会使现有登录会话失效）。
