from typing import List, Optional
from fastapi import HTTPException, Depends
from ..models.database import get_db
from ..models.schemas import Game, GameCreate, Player, Round, Score, GameAnalytics
from ..utils.validation import validation_service
from ..services.auth import auth_service
import uuid


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
            game_record = {
                "created_by": str(creator.uuid),
                "score_cutoff": game_data.score_cutoff
            }
            result = db.table("games").insert(game_record).execute()
            
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create game")
            
            game = Game(**result.data[0])
            
            # Create players
            players = []
            for name in game_data.player_names:
                player_record = {
                    "game_id": str(game.uuid),
                    "name": name.strip()
                }
                player_result = db.table("players").insert(player_record).execute()
                if player_result.data:
                    players.append(Player(**player_result.data[0]))
            
            game.players = players
            return game
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")

    async def get_game(self, game_id: uuid.UUID) -> Game:
        """Get game details with players"""
        db = get_db()
        
        # Get game
        result = db.table("games").select("*").eq("uuid", str(game_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game = Game(**result.data[0])
        
        # Get players
        players_result = db.table("players").select("*").eq("game_id", str(game_id)).execute()
        game.players = [Player(**player) for player in players_result.data]
        
        return game

    async def add_round_scores(self, game_id: uuid.UUID, scores: List[int]) -> Round:
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
            rounds_result = db.table("rounds").select("round_number").eq("game_id", str(game_id)).order("round_number", desc=True).limit(1).execute()
            current_round = rounds_result.data[0]["round_number"] + 1 if rounds_result.data else 1
            
            # Create round
            round_record = {
                "game_id": str(game_id),
                "round_number": current_round
            }
            round_result = db.table("rounds").insert(round_record).execute()
            
            if not round_result.data:
                raise HTTPException(status_code=500, detail="Failed to create round")
            
            round = Round(**round_result.data[0])
            
            # Add scores for each player
            for i, player in enumerate(game.players):
                points = scores[i]
                
                # Calculate cumulative total
                prev_scores = db.table("scores").select("cumulative_total").eq("player_id", str(player.uuid)).order("created_at", desc=True).limit(1).execute()
                prev_total = prev_scores.data[0]["cumulative_total"] if prev_scores.data else 0
                cumulative_total = prev_total + points
                
                # Update player total
                db.table("players").update({"total_score": cumulative_total}).eq("uuid", str(player.uuid)).execute()
                
                # Create score record
                score_record = {
                    "player_id": str(player.uuid),
                    "round_id": str(round.uuid),
                    "points": points,
                    "cumulative_total": cumulative_total
                }
                db.table("scores").insert(score_record).execute()
            
            # Check for game completion
            await self._check_game_completion(game_id, game.score_cutoff)
            
            return round
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add round: {str(e)}")

    async def get_game_analytics(self, game_id: uuid.UUID) -> GameAnalytics:
        """Get game analytics including standings"""
        game = await self.get_game(game_id)
        
        # Get current round
        db = get_db()
        rounds_result = db.table("rounds").select("round_number").eq("game_id", str(game_id)).order("round_number", desc=True).limit(1).execute()
        current_round = rounds_result.data[0]["round_number"] if rounds_result.data else 0
        
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

    async def _check_game_completion(self, game_id: uuid.UUID, score_cutoff: int):
        """Check if game should end using rummy elimination rules.

        Players are eliminated when they reach/exceed the cutoff.
        Game ends when only one player remains below the cutoff — that player wins.
        """
        db = get_db()

        # Get all players for this game
        all_players = db.table("players").select("*").eq("game_id", str(game_id)).execute()

        if not all_players.data or len(all_players.data) <= 1:
            return

        # Players still alive (below cutoff)
        alive = [p for p in all_players.data if p["total_score"] < score_cutoff]

        # Game ends when only 1 player remains below cutoff
        if len(alive) <= 1:
            winner = alive[0] if alive else min(all_players.data, key=lambda p: p["total_score"])
            db.table("games").update({
                "is_completed": True,
                "winner_id": winner["uuid"]
            }).eq("uuid", str(game_id)).execute()

    async def cancel_game(self, game_id: uuid.UUID, user_email: str):
        """Cancel a game. Only the creator can cancel."""
        db = get_db()

        # Get the game
        game = await self.get_game(game_id)

        # Get the user
        user = await auth_service.get_or_create_user(user_email)

        # Verify ownership
        if str(game.created_by) != str(user.uuid):
            raise HTTPException(status_code=403, detail="Only the game creator can cancel a game")

        if game.is_completed:
            raise HTTPException(status_code=400, detail="Cannot cancel a completed game")

        if game.is_cancelled:
            raise HTTPException(status_code=400, detail="Game is already cancelled")

        db.table("games").update({
            "is_cancelled": True
        }).eq("uuid", str(game_id)).execute()


game_service = GameService()