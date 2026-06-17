# DCF 计算器项目实现与部署文档

## 1. 项目概述

本项目是部署在 `vi.starbugs.net` 的 Django Web 应用，用于进行 DCF（Discounted Cash Flow，自由现金流折现）估值计算。

主要功能：

- DCF 计算器页面，三栏布局：标签/收藏侧栏 · 输入参数 · 估值结果
- 输入即时计算：前端 JS 实时计算估值结果、年度现金流明细与敏感性分析（无需提交）
- 整体视觉风格参考 `/root/dcf-calculator.html`（米白底 + 墨绿主色 `--accent:#2f6f4e`，圆角面板）
- 用户注册、登录、退出
- 登录用户可收藏已计算过的公司估值记录（点击「保存到收藏」提交，由服务端计算并入库）
- 收藏历史在左侧边栏按标签/分类展示，并支持折叠
- 点击某条收藏即可把当时填写的全部参数回填到输入表单并实时重算
- 左侧边栏分为「标签管理」与「我的收藏」两块，标签与具体股票收藏分开展示
- 登录后可先创建标签，例如消费板块、有色、科技、医药
- 可删除标签；标签名旁显示该标签下收藏数量
- 标签下若还有收藏，删除时弹窗提示且禁止删除，需先删完收藏（前端拦截 + 后端校验双重保证）
- 可删除单条股票收藏（左侧边栏及 /favorites/ 页面均提供删除）
- 计算时从已创建标签中选择分类，不再手动输入标签
- 每个 DCF 参数标签旁提供问号说明（鼠标悬停显示），帮助用户理解参数含义
- 单一页面标题（顶栏「DCF 估值计算器」），不再重复
- Nginx HTTPS/HTTP2/HTTP3 入口
- Gunicorn 运行 Django 应用
- SQLite 保存用户和收藏数据

项目目录：

```text
/var/www/vi.starbugs.net
```

## 2. 技术栈

后端：

- Python 3.12
- Django 6.0.6
- Gunicorn 26.0.0
- SQLite

前端：

- Django Template
- 原生 CSS
- 少量原生 JavaScript

部署：

- systemd 管理 Gunicorn 服务
- Nginx 1.31.1 反向代理
- Let's Encrypt HTTPS 证书
- HTTP 自动跳转 HTTPS
- HTTP/2、HTTP/3 已开启

选择 Django Template + 原生 CSS/JS 的原因：

- 当前功能以表单、登录、收藏记录为主，不需要复杂 SPA
- 不引入 Node/Vite/React 等额外构建链，部署更简单
- Django 自带认证、表单、CSRF、防护机制，适合快速实现登录和数据保存

## 3. 关键文件

```text
/var/www/vi.starbugs.net/manage.py
/var/www/vi.starbugs.net/dcfsite/settings.py
/var/www/vi.starbugs.net/dcfsite/urls.py
/var/www/vi.starbugs.net/calculator/models.py
/var/www/vi.starbugs.net/calculator/forms.py
/var/www/vi.starbugs.net/calculator/views.py
/var/www/vi.starbugs.net/calculator/urls.py
/var/www/vi.starbugs.net/calculator/templates/calculator/base.html
/var/www/vi.starbugs.net/calculator/templates/calculator/calculator.html
/var/www/vi.starbugs.net/calculator/templates/calculator/favorites.html
/var/www/vi.starbugs.net/calculator/templates/registration/login.html
/var/www/vi.starbugs.net/calculator/templates/registration/register.html
/var/www/vi.starbugs.net/calculator/static/calculator/style.css
/var/www/vi.starbugs.net/db.sqlite3
/var/www/vi.starbugs.net/requirements.txt
/var/www/vi.starbugs.net/staticfiles/
```

部署相关文件：

```text
/etc/systemd/system/dcfsite.service
/etc/nginx/conf.d/vi.starbugs.net.conf
/etc/letsencrypt/live/vi.starbugs.net/fullchain.pem
/etc/letsencrypt/live/vi.starbugs.net/privkey.pem
```

## 4. 数据存储

当前使用 SQLite：

```text
/var/www/vi.starbugs.net/db.sqlite3
```

用户注册、登录相关数据使用 Django 默认认证表：

```text
auth_user
auth_group
auth_permission
django_session
```

DCF 收藏记录保存在：

```text
calculator_dcfcalculation
```

模型文件：

```text
/var/www/vi.starbugs.net/calculator/models.py
```

核心模型：`DcfCalculation`。

保存字段包括：

- 用户
- 公司名称
- 股票代码
- 当前自由现金流
- 显式期增长率
- 折现率/WACC
- 永续增长率
- 预测年数
- 净有息债务
- 非经营性资产
- 总股本
- 企业价值
- 股权价值
- 每股价值
- 创建时间

## 5. DCF 计算逻辑

计算逻辑在：

```text
/var/www/vi.starbugs.net/calculator/views.py
```

核心函数：

```python
calculate_dcf(data)
```

计算过程：

1. 将用户输入的百分比参数除以 100 转换成小数
2. 从当前 FCFF 开始，按显式期增长率逐年预测自由现金流
3. 每年 FCFF 按折现率折现到当前
4. 用 Gordon Growth 永续增长模型计算终值
5. 将终值折现到当前
6. 得到企业价值 EV
7. 用 `企业价值 - 净债务 + 非经营性资产` 得到股权价值
8. 用 `股权价值 / 总股本` 得到每股价值

公式：

```text
企业价值 EV = Σ(FCFFt / (1 + WACC)^t) + Terminal Value / (1 + WACC)^n
Terminal Value = FCFn × (1 + g) / (WACC - g)
股权价值 = EV - 净有息债务 + 非经营性资产
每股价值 = 股权价值 / 总股本
```

表单校验：

- 永续增长率必须低于折现率
- 预测年数必须大于等于 1
- 总股本必须大于 0

## 6. 登录与收藏实现

登录、注册使用 Django 内置认证系统。

路由文件：

```text
/var/www/vi.starbugs.net/calculator/urls.py
```

路由：

```text
/                          DCF 计算器首页
/favorites/                我的收藏
/favorites/<pk>/delete/    删除单条收藏（POST）
/tags/<pk>/delete/         删除标签（POST，仅当标签下无收藏时允许）
/login/                    登录
/logout/                   退出
/register/                 注册
/admin/                    Django 管理后台
```

注册表单：

```text
/var/www/vi.starbugs.net/calculator/forms.py
```

计算与收藏逻辑：

- 估值结果由前端 JS（`calculator.html` 内联脚本）实时计算，未登录也可使用；JS 通过 Django 自动生成的字段 id（`id_current_fcf`、`id_growth_rate` 等）读取输入
- 表单提交（`action=calculate`）仅用于「保存到收藏」，因此需要登录；服务端 `calculate_dcf` 重新计算并把结果与全部参数写入 `calculator_dcfcalculation`，再 PRG 重定向回首页
- 已移除原先的 `save_to_favorites` 勾选项，保存改为显式按钮
- 点击收藏：每条收藏在 `.fav-load` 上以 `data-*` 携带全部参数，JS 回填到表单字段并触发实时重算
- 首页左侧边栏「我的收藏」按标签分组展示当前用户全部收藏（仅显示有收藏的分组）
- `/favorites/` 显示当前用户全部收藏记录，并可逐条删除
- 删除收藏：`delete_favorite` 视图按 `user+pk` 过滤删除，POST 提交
- 删除标签：`delete_tag` 视图先统计该标签名下收藏数量，大于 0 时返回 error 消息并拒绝删除，为 0 时才真正删除；前端对有收藏的标签用 `alert` 拦截，不提交表单

## 7. 参数问号说明

每个 DCF 参数的说明写在 Django Form 的 `help_texts` 中：

```text
/var/www/vi.starbugs.net/calculator/forms.py
```

字段渲染统一通过局部模板：

```text
/var/www/vi.starbugs.net/calculator/templates/calculator/_field.html
```

该模板为每个带 `help_text` 的字段渲染一个 `?` 小圆点，鼠标悬停（`title` 属性）显示说明；可选 `suffix` 参数用于在输入框右侧显示单位（如 `%`、`年`）。

## 8. Python 虚拟环境

虚拟环境位置：

```text
/var/www/vi.starbugs.net/.venv
```

依赖文件：

```text
/var/www/vi.starbugs.net/requirements.txt
```

当前主要依赖：

```text
Django==6.0.6
gunicorn==26.0.0
asgiref==3.11.1
sqlparse==0.5.5
packaging==26.2
```

重新安装依赖：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/pip install -r requirements.txt
```

## 9. Django 关键配置

配置文件：

```text
/var/www/vi.starbugs.net/dcfsite/settings.py
```

关键配置：

```python
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
CSRF_TRUSTED_ORIGINS = ['https://vi.starbugs.net']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
LOGIN_REDIRECT_URL = 'calculator'
LOGOUT_REDIRECT_URL = 'calculator'
```

`SECRET_KEY`、`DEBUG`、`ALLOWED_HOSTS` 现在从环境变量读取，不再硬编码在 `settings.py`：

```python
DEBUG = os.environ.get('DJANGO_DEBUG', '0') in ('1', 'true', ...)   # 默认关闭
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']                         # DEBUG 关闭时必须提供，否则启动报错
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '...').split(',')
```

当 `DEBUG = False` 时自动启用生产安全配置：

```python
SECURE_SSL_REDIRECT = True            # 明文 HTTP 跳转 HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000        # HSTS 一年，含子域，preload
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

环境变量保存在 `/etc/dcfsite.env`（权限 `640`，属主 `root:www-data`，不纳入代码库），由 systemd 通过 `EnvironmentFile` 注入：

```ini
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<随机生成的密钥>
DJANGO_ALLOWED_HOSTS=vi.starbugs.net,localhost,127.0.0.1
```

> 注：生产 `ALLOWED_HOSTS` 已移除 `testserver`（仅运行测试时需要）。
> 轮换密钥：生成新值写入 `/etc/dcfsite.env` 后 `systemctl restart dcfsite.service`（会使现有登录会话失效）。
> 本地开发：`DJANGO_DEBUG=1 .venv/bin/python manage.py runserver`，无需设置密钥。

部署前自检：

```bash
.venv/bin/python manage.py check --deploy
```

静态文件收集命令：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/python manage.py collectstatic --noinput
```

## 10. Gunicorn 服务

systemd 服务文件：

```text
/etc/systemd/system/dcfsite.service
```

内容：

```ini
[Unit]
Description=DCF calculator Django app
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/vi.starbugs.net
Environment="PATH=/var/www/vi.starbugs.net/.venv/bin"
EnvironmentFile=/etc/dcfsite.env
ExecStart=/var/www/vi.starbugs.net/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 dcfsite.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

服务管理命令：

```bash
systemctl status dcfsite.service --no-pager
systemctl restart dcfsite.service
systemctl stop dcfsite.service
systemctl start dcfsite.service
systemctl enable dcfsite.service
journalctl -u dcfsite.service -f
```

当前 Gunicorn 监听：

```text
127.0.0.1:8000
```

只监听本机，由 Nginx 对外代理。

## 11. Nginx 配置

站点配置：

```text
/etc/nginx/conf.d/vi.starbugs.net.conf
```

当前配置：

```nginx
server {
    listen 80;
    server_name vi.starbugs.net;

    location /.well-known/acme-challenge/ {
        root /var/www/vi.starbugs.net;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    listen 443 quic reuseport;
    http2 on;
    http3 on;

    server_name vi.starbugs.net;

    ssl_certificate /etc/letsencrypt/live/vi.starbugs.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vi.starbugs.net/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    add_header Alt-Svc 'h3=":443"; ma=86400' always;
    add_header QUIC-Status $http3 always;

    location /static/ {
        alias /var/www/vi.starbugs.net/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

检查并重载：

```bash
nginx -t
systemctl reload nginx
```

## 12. 部署过程记录

本次部署执行了以下步骤：

1. 查看 `/var/local/docs` 下 DCF 文档
2. 创建 Django 项目 `dcfsite`
3. 创建 Django 应用 `calculator`
4. 实现 DCF 计算模型、表单、视图、模板和样式
5. 使用 SQLite 创建数据库
6. 执行迁移：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/python manage.py makemigrations calculator
.venv/bin/python manage.py migrate
```

7. 安装 Gunicorn：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/pip install -i https://pypi.org/simple gunicorn
.venv/bin/pip freeze > requirements.txt
```

8. 配置静态文件目录并收集静态文件：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/python manage.py collectstatic --noinput
```

9. 创建 systemd 服务：

```text
/etc/systemd/system/dcfsite.service
```

10. 启动并设置开机自启：

```bash
systemctl daemon-reload
systemctl enable --now dcfsite.service
```

11. 修改 Nginx，将 HTTPS 请求代理到 `127.0.0.1:8000`
12. 验证 Nginx 配置并重载：

```bash
nginx -t
systemctl reload nginx
```

## 13. 验证结果

Django 配置检查：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/python manage.py check
```

结果：

```text
System check identified no issues (0 silenced).
```

测试：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/python manage.py test
```

结果：

```text
Ran 1 test
OK
```

Gunicorn 本地访问：

```bash
curl --noproxy '*' -I http://127.0.0.1:8000/
```

结果：

```text
HTTP/1.1 200 OK
Server: gunicorn
```

Nginx HTTPS 反向代理访问：

```bash
curl --noproxy '*' -I --http2 --resolve vi.starbugs.net:443:127.0.0.1 https://vi.starbugs.net/
```

结果：

```text
HTTP/2 200
server: nginx/1.31.1
```

静态文件访问：

```bash
curl --noproxy '*' -I --http2 --resolve vi.starbugs.net:443:127.0.0.1 https://vi.starbugs.net/static/calculator/style.css
```

结果：

```text
HTTP/2 200
content-type: text/css
```

## 14. 日常维护

修改 Python/Django 代码后：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/python manage.py check
.venv/bin/python manage.py test
systemctl restart dcfsite.service
```

修改静态文件后：

```bash
cd /var/www/vi.starbugs.net
.venv/bin/python manage.py collectstatic --noinput
systemctl reload nginx
```

修改 Nginx 配置后：

```bash
nginx -t
systemctl reload nginx
```

查看 Django/Gunicorn 日志：

```bash
journalctl -u dcfsite.service -f
```

查看 Nginx 状态：

```bash
systemctl status nginx --no-pager
```

查看 Nginx 错误日志：

```bash
/var/log/nginx/error.log
```

## 15. 注意事项

- 当前数据库是 SQLite，适合小规模使用；如果后续用户量增长，建议迁移到 PostgreSQL。
- `DEBUG` 默认为 `False`，`SECRET_KEY` 已移到 `/etc/dcfsite.env` 环境变量中（见第 9 节）；备份服务器时需一并备份该文件。
- `db.sqlite3` 包含用户和收藏数据，备份时必须包含该文件。
- `/var/www/vi.starbugs.net/staticfiles/` 是 collectstatic 生成目录，不是源文件目录。
- Nginx 只代理动态请求，静态文件由 Nginx 直接返回。
- Gunicorn 只监听 `127.0.0.1:8000`，不会直接暴露到公网。
- 证书续期仍使用 `/.well-known/acme-challenge/` 路径，Nginx 已保留该配置。
