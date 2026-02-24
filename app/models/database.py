from supabase import create_client
from ..config import settings
from typing import Optional


class Database:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def connect(self):
        if self._client is None:
            self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    def get_client(self):
        return self.connect()


# Singleton instance
db = Database()


def handle_db_error(result, operation="database operation"):
    """Handle Supabase database errors consistently"""
    if result.get('error'):
        raise HTTPException(status_code=400, detail=f"{operation.capitalize()} failed: {result['error']}")
    return result.get('data', [])


def get_db():
    """FastAPI dependency for database access"""
    return db.get_client()