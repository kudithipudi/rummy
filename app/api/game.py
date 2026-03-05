from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import uuid
import json
from ..services.game import game_service
from ..services.auth import auth_service
from ..models.schemas import GameCreate, Game, Player
from ..models.database import get_db
from ..config import settings
from fastapi import status

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_template_context(request: Request, **kwargs):
    """Create template context with base_path included"""
    return {
        "request": request,
        "base_path": settings.base_path,
        **kwargs
    }


async def get_current_user(request: Request):
    """Get current user from cookie"""
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        return None

    try:
        email = auth_service.verify_token(auth_token)
        user = await auth_service.get_or_create_user(email)
        return user
    except:
        return None


@router.get("/dashboard")
async def dashboard_page(request: Request):
    """Display dashboard with active and historical games"""
    current_user = await get_current_user(request)
    if not current_user:
        return RedirectResponse(url=f"{settings.base_path}/auth/login", status_code=302)

    db = get_db()

    # Get all games created by this user
    games_data = db.execute_query(
        "SELECT * FROM games WHERE created_by = ? ORDER BY created_at DESC",
        (str(current_user.uuid),)
    )

    active_games = []
    historical_games = []

    for game_data in games_data:
        game = Game(**game_data)

        # Get players for this game
        players_data = db.execute_query(
            "SELECT * FROM players WHERE game_id = ?", (str(game.uuid),)
        )
        game.players = [Player(**p) for p in players_data]

        # Get round count
        last_round = db.execute_query(
            "SELECT round_number FROM rounds WHERE game_id = ? ORDER BY round_number DESC LIMIT 1",
            (str(game.uuid),), fetchone=True
        )
        round_count = last_round["round_number"] if last_round else 0

        game_info = {
            "game": game,
            "round_count": round_count,
        }

        # Find winner name if completed
        if game.is_completed and game.winner_id:
            winner_player = next((p for p in game.players if str(p.uuid) == str(game.winner_id)), None)
            game_info["winner_name"] = winner_player.name if winner_player else "Unknown"

        if not game.is_completed and not game.is_cancelled:
            active_games.append(game_info)
        else:
            historical_games.append(game_info)

    return templates.TemplateResponse("game/dashboard.html", get_template_context(
        request,
        user=current_user,
        active_games=active_games,
        historical_games=historical_games,
    ))


@router.get("/new")
async def new_game_page(request: Request):
    """Display game setup page"""
    current_user = await get_current_user(request)
    if not current_user:
        return RedirectResponse(url=f"{settings.base_path}/auth/login", status_code=302)

    return templates.TemplateResponse("game/setup.html", get_template_context(
        request,
        user=current_user
    ))


@router.post("/create")
async def create_game(
    request: Request,
    player_names: str = Form(...),
    score_cutoff: int = Form(...),
    num_players: int = Form(...)
):
    """Create a new game"""
    current_user = await get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Parse player names
    names = [name.strip() for name in player_names.split(',') if name.strip()]
    if len(names) != num_players:
        raise HTTPException(status_code=400, detail="Number of names doesn't match specified count")

    # Create game
    game_data = GameCreate(
        player_names=names,
        score_cutoff=score_cutoff
    )

    game = await game_service.create_game(game_data, current_user.email)

    return RedirectResponse(url=f"{settings.base_path}/game/{game.uuid}", status_code=302)


@router.post("/{game_id}/cancel")
async def cancel_game(request: Request, game_id: uuid.UUID):
    """Cancel a game"""
    current_user = await get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    await game_service.cancel_game(game_id, current_user.email)

    return RedirectResponse(url=f"{settings.base_path}/game/dashboard", status_code=302)


@router.get("/{game_id}")
async def game_page(request: Request, game_id: uuid.UUID):
    """Display game scoring page"""
    current_user = await get_current_user(request)
    game = await game_service.get_game(game_id)
    analytics = await game_service.get_game_analytics(game_id)

    db = get_db()

    # Get all rounds with scores
    rounds_data = db.execute_query(
        "SELECT * FROM rounds WHERE game_id = ? ORDER BY round_number",
        (str(game_id),)
    )

    rounds_with_scores = []
    for round_data in rounds_data:
        scores_data = db.execute_query(
            "SELECT s.*, p.name as player_name FROM scores s JOIN players p ON s.player_id = p.uuid WHERE s.round_id = ?",
            (round_data["uuid"],)
        )

        round_scores = {}
        for score_data in scores_data:
            round_scores[score_data["player_name"]] = score_data

        rounds_with_scores.append({
            "round": round_data,
            "scores": round_scores
        })

    # Check if current user is the creator
    is_creator = current_user and str(current_user.uuid) == str(game.created_by)

    return templates.TemplateResponse("game/play.html", get_template_context(
        request,
        game=game,
        user=current_user,
        is_creator=is_creator,
        analytics=analytics,
        rounds=rounds_with_scores,
        players_json=json.dumps([p.model_dump(mode='json') for p in game.players]),
        analytics_json=json.dumps(analytics.model_dump(mode='json')),
        rounds_json=json.dumps(rounds_with_scores, default=str),
    ))


@router.post("/{game_id}/round")
async def add_round(
    request: Request,
    game_id: uuid.UUID,
    score_entries: List[str] = Form(...)
):
    """Add a new round with scores"""
    current_user = await get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Parse scores
    scores = []
    for score_str in score_entries:
        try:
            score = int(score_str)
            if score < 0:
                raise HTTPException(status_code=400, detail="Scores must be non-negative")
            scores.append(score)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid score format")

    # Add round
    await game_service.add_round_scores(game_id, scores)

    return RedirectResponse(url=f"{settings.base_path}/game/{game_id}", status_code=302)


@router.get("/{game_id}/analytics")
async def game_analytics(game_id: uuid.UUID):
    """Get game analytics as JSON"""
    analytics = await game_service.get_game_analytics(game_id)
    return analytics
