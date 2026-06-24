"""数据库路由：保证 stock 连接只读复用。

calculator 的 model 全部走 default（dcf_data / sqlite）。stock 连接指向
stock_crawler 的 stock_data 库，DCF 站只通过原生 SQL 读取它，不应在该连接上
建表或迁移。这里显式把迁移限制在 default，并拒绝在 stock 上跑 migrate。
"""


class StockReadOnlyRouter:
    def db_for_read(self, model, **hints):
        # 所有 ORM model 仍走 default；stock 库仅由原生 cursor 读取。
        return 'default'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # 只允许在 default 上迁移；stock 永不迁移。
        return db == 'default'
