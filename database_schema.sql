-- Rummy Score Tracker Database Schema
-- Copy this to your Supabase SQL editor

-- Users table (for authentication)
CREATE TABLE users (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Games table (without foreign keys initially)
CREATE TABLE games (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID,
    score_cutoff INTEGER NOT NULL CHECK (score_cutoff > 0),
    is_completed BOOLEAN DEFAULT FALSE,
    is_cancelled BOOLEAN DEFAULT FALSE,
    winner_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players table  
CREATE TABLE players (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID,
    name VARCHAR(100) NOT NULL,
    total_score INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(game_id, name) -- No duplicate names in same game
);

-- Add foreign key constraints after both tables exist
ALTER TABLE games ADD CONSTRAINT fk_games_created_by 
    FOREIGN KEY (created_by) REFERENCES users(uuid);
ALTER TABLE games ADD CONSTRAINT fk_games_winner_id 
    FOREIGN KEY (winner_id) REFERENCES players(uuid);
ALTER TABLE players ADD CONSTRAINT fk_players_game_id 
    FOREIGN KEY (game_id) REFERENCES games(uuid) ON DELETE CASCADE;

-- Rounds table
CREATE TABLE rounds (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID REFERENCES games(uuid) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(game_id, round_number) -- No duplicate round numbers in same game
);

-- Scores table
CREATE TABLE scores (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(uuid) ON DELETE CASCADE,
    round_id UUID REFERENCES rounds(uuid) ON DELETE CASCADE,
    points INTEGER NOT NULL CHECK (points >= 0),
    cumulative_total INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, round_id) -- One score per player per round
);

-- Indexes for better performance
CREATE INDEX idx_games_created_by ON games(created_by);
CREATE INDEX idx_games_created_at ON games(created_at);
CREATE INDEX idx_players_game_id ON players(game_id);
CREATE INDEX idx_rounds_game_id ON rounds(game_id);
CREATE INDEX idx_scores_player_id ON scores(player_id);
CREATE INDEX idx_scores_round_id ON scores(round_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_games_updated_at 
    BEFORE UPDATE ON games 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate player rankings
CREATE OR REPLACE FUNCTION calculate_player_rankings(game_uuid UUID)
RETURNS TABLE (
    player_uuid UUID,
    player_name VARCHAR,
    total_score INTEGER,
    rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.uuid,
        p.name,
        p.total_score,
        RANK() OVER (ORDER BY p.total_score ASC)
    FROM players p
    WHERE p.game_id = game_uuid
    ORDER BY p.total_score ASC;
END;
$$ LANGUAGE plpgsql;