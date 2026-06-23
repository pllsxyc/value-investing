import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "stock_user"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "stock_data"),
    "charset": "utf8mb4",
    "autocommit": False,
}

CRAWLER_SLEEP_SECONDS = float(os.getenv("CRAWLER_SLEEP_SECONDS", "1.5"))
SKIP_NON_TRADING_DAY = os.getenv("SKIP_NON_TRADING_DAY", "true").lower() == "true"
