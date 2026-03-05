#!/bin/bash
# SQLite backup script for Rummy Score Tracker

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DB_PATH="$PROJECT_DIR/data/rummy.db"
BACKUP_DIR="$PROJECT_DIR/data/backups"

mkdir -p "$BACKUP_DIR"

# SQLite online backup
sqlite3 "$DB_PATH" ".backup $BACKUP_DIR/rummy_$(date +%Y%m%d_%H%M%S).db"

# Keep last 30 days
find "$BACKUP_DIR" -name "rummy_*.db" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR"
