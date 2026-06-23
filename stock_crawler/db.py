import threading
from contextlib import contextmanager
from datetime import datetime

import pandas as pd
import pymysql

from stock_crawler.config import MYSQL_CONFIG

_local = threading.local()


@contextmanager
def session():
    """Open one connection reused by every execute_*/fetch_* call inside the block."""
    conn = pymysql.connect(**MYSQL_CONFIG)
    _local.conn = conn
    try:
        yield conn
    finally:
        _local.conn = None
        conn.close()


@contextmanager
def get_connection():
    shared = getattr(_local, "conn", None)
    if shared is not None:
        # Reuse the session connection; commit per statement, leave it open for session() to close.
        try:
            yield shared
            shared.commit()
        except Exception:
            shared.rollback()
            raise
        return
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
