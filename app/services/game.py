from typing import List, Optional
from fastapi import HTTPException
from ..models.database import get_db
from ..models.schemas import Game, GameCreate, Player, Round, Score, GameAnalytics
from ..utils.validation import validation_service
from ..services.auth import auth_service
import uuid as uuid_mod
from datetime import datetime, timezone


class GameService:
    def __init__(self):
        pass

    async def create_game(self, game_data: GameCreate, creator_email: str) -> Game:
        """Create a new game with players"""

        # Validate game setup
        is_valid, error_msg = validation_service.validate_game_setup(
            game_data.player_names,
            game_data.score_cutoff
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        db = get_db()

        try:
            # Get or create user
            creator = await auth_service.get_or_create_user(creator_email)

            # Create game
            game_uuid = str(uuid_mod.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            db.execute_insert(
                "INSERT INTO games (uuid, created_by, score_cutoff, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (game_uuid, str(creator.uuid), game_data.score_cutoff, now, now)
            )

            game_row = db.execute_query(
                "SELECT * FROM games WHERE uuid = ?", (game_uuid,), fetchone=True
            )
            if not game_row:
                raise HTTPException(status_code=500, detail="Failed to create game")

            game = Game(**game_row)

            # Create players
            players = []
            for name in game_data.player_names:
                player_uuid = str(uuid_mod.uuid4())
                db.execute_insert(
                    "INSERT INTO players (uuid, game_id, name, created_at) VALUES (?, ?, ?, ?)",
                    (player_uuid, game_uuid, name.strip(), now)
                )
                player_row = db.execute_query(
                    "SELECT * FROM players WHERE uuid = ?", (player_uuid,), fetchone=True
                )
                if player_row:
                    players.append(Player(**player_row))

            game.players = players
            return game

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")

    async def get_game(self, game_id: uuid_mod.UUID) -> Game:
        """Get game details with players"""
        db = get_db()

        # Get game
        game_row = db.execute_query(
            "SELECT * FROM games WHERE uuid = ?", (str(game_id),), fetchone=True
        )
        if not game_row:
            raise HTTPException(status_code=404, detail="Game not found")

        game = Game(**game_row)

        # Get players
        players_rows = db.execute_query(
            "SELECT * FROM players WHERE game_id = ? ORDER BY created_at", (str(game_id),)
        )
        game.players = [Player(**p) for p in players_rows]

        return game

    async def add_round_scores(self, game_id: uuid_mod.UUID, scores: List[int]) -> Round:
        """Add a new round with scores for all players"""
        db = get_db()

        # Get game and players
        game = await self.get_game(game_id)

        # Block rounds on completed or cancelled games
        if game.is_completed:
            raise HTTPException(status_code=400, detail="Cannot add rounds to a completed game")
        if game.is_cancelled:
            raise HTTPException(status_code=400, detail="Cannot add rounds to a cancelled game")

        if len(scores) != len(game.players):
            raise HTTPException(status_code=400, detail="Score count must match player count")

        try:
            # Get current round number
            last_round = db.execute_query(
                "SELECT round_number FROM rounds WHERE game_id = ? ORDER BY round_number DESC LIMIT 1",
                (str(game_id),), fetchone=True
            )
            current_round = (last_round["round_number"] + 1) if last_round else 1

            # Create round
            round_uuid = str(uuid_mod.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            db.execute_insert(
                "INSERT INTO rounds (uuid, game_id, round_number, created_at) VALUES (?, ?, ?, ?)",
                (round_uuid, str(game_id), current_round, now)
            )

            round_row = db.execute_query(
                "SELECT * FROM rounds WHERE uuid = ?", (round_uuid,), fetchone=True
            )
            if not round_row:
                raise HTTPException(status_code=500, detail="Failed to create round")

            round_obj = Round(**round_row)

            # Add scores for each player using a single connection for atomicity
            with db.get_connection() as conn:
                for i, player in enumerate(game.players):
                    points = scores[i]

                    # Get previous cumulative total
                    cursor = conn.execute(
                        "SELECT cumulative_total FROM scores WHERE player_id = ? ORDER BY created_at DESC LIMIT 1",
                        (str(player.uuid),)
                    )
                    prev_row = cursor.fetchone()
                    prev_total = prev_row["cumulative_total"] if prev_row else 0
                    cumulative_total = prev_total + points

                    # Update player total
                    conn.execute(
                        "UPDATE players SET total_score = ? WHERE uuid = ?",
                        (cumulative_total, str(player.uuid))
                    )

                    # Create score record
                    score_uuid = str(uuid_mod.uuid4())
                    conn.execute(
                        "INSERT INTO scores (uuid, player_id, round_id, points, cumulative_total, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (score_uuid, str(player.uuid), round_uuid, points, cumulative_total, now)
                    )

            # Check for game completion
            await self._check_game_completion(game_id, game.score_cutoff)

            return round_obj

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add round: {str(e)}")

    async def get_game_analytics(self, game_id: uuid_mod.UUID) -> GameAnalytics:
        """Get game analytics including standings"""
        game = await self.get_game(game_id)

        # Get current round
        db = get_db()
        last_round = db.execute_query(
            "SELECT round_number FROM rounds WHERE game_id = ? ORDER BY round_number DESC LIMIT 1",
            (str(game_id),), fetchone=True
        )
        current_round = last_round["round_number"] if last_round else 0

        # Sort players by score (ascending - lowest score wins)
        sorted_players = sorted(game.players, key=lambda p: p.total_score)
        leader = sorted_players[0] if sorted_players else None

        # Calculate points to win for each player
        points_to_win = []
        for player in game.players:
            points_needed = game.score_cutoff - player.total_score
            if points_needed < 0:
                points_needed = 0
            points_to_win.append({
                "player_name": player.name,
                "points_needed": points_needed
            })

        return GameAnalytics(
            game_id=game_id,
            current_round=current_round,
            players=game.players,
            leader=leader,
            points_to_win=points_to_win
        )

    async def _check_game_completion(self, game_id: uuid_mod.UUID, score_cutoff: int):
        """Check if game should end using rummy elimination rules."""
        db = get_db()

        all_players = db.execute_query(
            "SELECT * FROM players WHERE game_id = ?", (str(game_id),)
        )

        if not all_players or len(all_players) <= 1:
            return

        # Players still alive (below cutoff)
        alive = [p for p in all_players if p["total_score"] < score_cutoff]

        # Game ends when only 1 player remains below cutoff
        if len(alive) <= 1:
            winner = alive[0] if alive else min(all_players, key=lambda p: p["total_score"])
            db.execute_insert(
                "UPDATE games SET is_completed = 1, winner_id = ? WHERE uuid = ?",
                (winner["uuid"], str(game_id))
            )

    async def cancel_game(self, game_id: uuid_mod.UUID, user_email: str):
        """Cancel a game. Only the creator can cancel."""
        db = get_db()

        game = await self.get_game(game_id)
        user = await auth_service.get_or_create_user(user_email)

        if str(game.created_by) != str(user.uuid):
            raise HTTPException(status_code=403, detail="Only the game creator can cancel a game")

        if game.is_completed:
            raise HTTPException(status_code=400, detail="Cannot cancel a completed game")

        if game.is_cancelled:
            raise HTTPException(status_code=400, detail="Game is already cancelled")

        db.execute_insert(
            "UPDATE games SET is_cancelled = 1 WHERE uuid = ?",
            (str(game_id),)
        )


game_service = GameService()
