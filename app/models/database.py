import sqlite3
import uuid
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class SQLiteDatabase:
    """SQLite database service for Rummy app."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = None):
        if not hasattr(self, '_initialized'):
            self.db_path = db_path or os.getenv("SQLITE_DB_PATH", "data/rummy.db")
            self._initialized = True
            self._ensure_schema()

    def _ensure_schema(self):
        """Initialize database schema if tables don't exist."""
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database_schema_sqlite.sql')
        if os.path.exists(schema_path):
            with self.get_connection() as conn:
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def generate_uuid() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def dict_from_row(row) -> Optional[Dict]:
        return dict(row) if row else None

    def execute_query(self, query: str, params: tuple = (), fetchone: bool = False) -> Any:
        """Execute a query and return results as list of dicts."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            if fetchone:
                row = cursor.fetchone()
                return self.dict_from_row(row)
            return [self.dict_from_row(row) for row in cursor.fetchall()]

    def execute_insert(self, query: str, params: tuple = ()) -> None:
        """Execute an insert/update query."""
        with self.get_connection() as conn:
            conn.execute(query, params)


# Singleton instance
db = SQLiteDatabase()


def get_db() -> SQLiteDatabase:
    """FastAPI dependency for database access."""
    return db
