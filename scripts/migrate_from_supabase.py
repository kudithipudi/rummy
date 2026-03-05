#!/usr/bin/env python3
"""Download data from Supabase and migrate to SQLite."""
import sqlite3
import os
import json
from supabase import create_client

# Supabase connection
SUPABASE_URL = 'https://lkrpodwqjzlgisvagmaj.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxrcnBvZHdxanpsZ2lzdmFnbWFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwOTg5MzYsImV4cCI6MjA4NDY3NDkzNn0.SVAZ3B3InHKrXLq0h7Hq3QbjTw6WRubDueLFw5w91ls'

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'rummy.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database_schema_sqlite.sql')


def init_sqlite(db_path, schema_path):
    """Initialize SQLite database with schema."""
    # Remove existing db if present
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")  # Disable during migration
    conn.execute("PRAGMA journal_mode = WAL")

    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    return conn


def migrate():
    """Migrate all data from Supabase to SQLite."""
    print(f"Connecting to Supabase: {SUPABASE_URL}")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"Initializing SQLite database: {SQLITE_DB_PATH}")
    conn = init_sqlite(SQLITE_DB_PATH, SCHEMA_PATH)
    cursor = conn.cursor()

    # Disable foreign keys during import
    cursor.execute("PRAGMA foreign_keys = OFF")

    # 1. Migrate users
    print("Migrating users...")
    users = supabase.table("users").select("*").execute()
    for user in users.data:
        cursor.execute(
            "INSERT INTO users (uuid, email, created_at, is_active) VALUES (?, ?, ?, ?)",
            (user['uuid'], user['email'], user['created_at'], 1 if user.get('is_active', True) else 0)
        )
    print(f"  Migrated {len(users.data)} users")

    # 2. Migrate games
    print("Migrating games...")
    games = supabase.table("games").select("*").execute()
    for game in games.data:
        cursor.execute(
            "INSERT INTO games (uuid, created_by, score_cutoff, is_completed, is_cancelled, winner_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                game['uuid'], game.get('created_by'), game['score_cutoff'],
                1 if game.get('is_completed', False) else 0,
                1 if game.get('is_cancelled', False) else 0,
                game.get('winner_id'), game['created_at'], game.get('updated_at', game['created_at'])
            )
        )
    print(f"  Migrated {len(games.data)} games")

    # 3. Migrate players
    print("Migrating players...")
    players = supabase.table("players").select("*").execute()
    for player in players.data:
        cursor.execute(
            "INSERT INTO players (uuid, game_id, name, total_score, created_at) VALUES (?, ?, ?, ?, ?)",
            (player['uuid'], player['game_id'], player['name'], player.get('total_score', 0), player['created_at'])
        )
    print(f"  Migrated {len(players.data)} players")

    # 4. Migrate rounds
    print("Migrating rounds...")
    rounds = supabase.table("rounds").select("*").execute()
    for round_data in rounds.data:
        cursor.execute(
            "INSERT INTO rounds (uuid, game_id, round_number, created_at) VALUES (?, ?, ?, ?)",
            (round_data['uuid'], round_data['game_id'], round_data['round_number'], round_data['created_at'])
        )
    print(f"  Migrated {len(rounds.data)} rounds")

    # 5. Migrate scores
    print("Migrating scores...")
    scores = supabase.table("scores").select("*").execute()
    for score in scores.data:
        cursor.execute(
            "INSERT INTO scores (uuid, player_id, round_id, points, cumulative_total, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (score['uuid'], score['player_id'], score['round_id'], score['points'], score['cumulative_total'], score['created_at'])
        )
    print(f"  Migrated {len(scores.data)} scores")

    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()

    print("\nMigration complete!")
    print(f"SQLite database created at: {SQLITE_DB_PATH}")


if __name__ == "__main__":
    migrate()
