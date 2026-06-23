from contextlib import contextmanager
from datetime import datetime

import pandas as pd
import pymysql

from stock_crawler.config import MYSQL_CONFIG


@contextmanager
def get_connection():
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def clean_value(value):
    if pd.isna(value):
        return None
    return value


def clean_params(params):
    if params is None:
        return None
    if isinstance(params, dict):
        return {key: clean_value(value) for key, value in params.items()}
    return tuple(clean_value(value) for value in params)


def execute_many(sql, rows):
    if not rows:
        return 0
    rows = [clean_params(row) for row in rows]
    with get_connection() as conn:
        with conn.cursor() as cursor:
            return cursor.executemany(sql, rows)


def execute_one(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            return cursor.execute(sql, clean_params(params) or ())


def fetch_all(sql, params=None):
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()


def log_job(job_name, stock_code, run_date, status, message, started_at, finished_at=None):
    execute_one(
        """
        INSERT INTO crawler_job_log
        (job_name, stock_code, run_date, status, message, started_at, finished_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            job_name,
            stock_code,
            run_date,
            status,
            message,
            started_at,
            finished_at or datetime.now(),
        ),
    )
