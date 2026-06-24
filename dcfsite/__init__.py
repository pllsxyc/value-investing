import pymysql

# 让 Django 的 MySQL 后端用纯 Python 的 PyMySQL 充当 MySQLdb（免编译 mysqlclient）
pymysql.install_as_MySQLdb()
