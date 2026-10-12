"""MySQL connection helper (PyMySQL)."""
import os
from contextlib import contextmanager
from pathlib import Path

import pymysql
from dotenv import load_dotenv

# Always read the .env that sits in this project folder.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def get_connection():
    """
    Open a new MySQL connection.

    Settings are read on every call so a changed .env / environment is
    respected. Timeouts make sure a dead database fails fast instead of
    hanging a web request forever.
    """
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=_int_env("DB_PORT", 3306),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD") or "monish@123",
        database=os.getenv("DB_NAME", "sanjivni_clinic"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=_int_env("DB_CONNECT_TIMEOUT", 5),
        read_timeout=_int_env("DB_READ_TIMEOUT", 15),
        write_timeout=_int_env("DB_WRITE_TIMEOUT", 15),
    )


@contextmanager
def get_db():
    """
    Transaction context manager.

    Commits when the block succeeds, rolls back when it raises, and always
    closes the connection.
    """
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
