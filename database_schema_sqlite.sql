-- Rummy Score Tracker SQLite Schema
-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Users table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    uuid TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1
);

-- Games table
CREATE TABLE IF NOT EXISTS games (
    uuid TEXT PRIMARY KEY,
    created_by TEXT,
    score_cutoff INTEGER NOT NULL CHECK (score_cutoff > 0),
    is_completed INTEGER DEFAULT 0,
    is_cancelled INTEGER DEFAULT 0,
    winner_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (created_by) REFERENCES users(uuid),
    FOREIGN KEY (winner_id) REFERENCES players(uuid)
);

-- Players table
CREATE TABLE IF NOT EXISTS players (
    uuid TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    name TEXT NOT NULL,
    total_score INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (game_id) REFERENCES games(uuid) ON DELETE CASCADE,
    UNIQUE(game_id, name)
);

-- Rounds table
CREATE TABLE IF NOT EXISTS rounds (
    uuid TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (game_id) REFERENCES games(uuid) ON DELETE CASCADE,
    UNIQUE(game_id, round_number)
);

-- Scores table
CREATE TABLE IF NOT EXISTS scores (
    uuid TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    points INTEGER NOT NULL CHECK (points >= 0),
    cumulative_total INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (player_id) REFERENCES players(uuid) ON DELETE CASCADE,
    FOREIGN KEY (round_id) REFERENCES rounds(uuid) ON DELETE CASCADE,
    UNIQUE(player_id, round_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_games_created_by ON games(created_by);
CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at);
CREATE INDEX IF NOT EXISTS idx_players_game_id ON players(game_id);
CREATE INDEX IF NOT EXISTS idx_rounds_game_id ON rounds(game_id);
CREATE INDEX IF NOT EXISTS idx_scores_player_id ON scores(player_id);
CREATE INDEX IF NOT EXISTS idx_scores_round_id ON scores(round_id);

-- Trigger to automatically update updated_at
CREATE TRIGGER IF NOT EXISTS update_games_updated_at
AFTER UPDATE ON games
FOR EACH ROW
BEGIN
    UPDATE games SET updated_at = datetime('now')
    WHERE uuid = NEW.uuid;
END;
