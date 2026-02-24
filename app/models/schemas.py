from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pass


class User(UserBase):
    uuid: UUID4
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class PlayerBase(BaseModel):
    name: str


class PlayerCreate(PlayerBase):
    game_id: UUID4


class Player(PlayerBase):
    uuid: UUID4
    game_id: UUID4
    total_score: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class GameBase(BaseModel):
    score_cutoff: int  # 100, 150, or 201


class GameCreate(GameBase):
    player_names: List[str]


class Game(GameBase):
    uuid: UUID4
    created_by: UUID4
    is_completed: bool = False
    is_cancelled: bool = False
    winner_id: Optional[UUID4] = None
    created_at: datetime
    players: List[Player] = []

    class Config:
        from_attributes = True


class ScoreBase(BaseModel):
    points: int


class ScoreCreate(ScoreBase):
    player_id: UUID4
    round_id: UUID4


class Score(ScoreBase):
    uuid: UUID4
    player_id: UUID4
    round_id: UUID4
    cumulative_total: int
    created_at: datetime

    class Config:
        from_attributes = True


class RoundBase(BaseModel):
    round_number: int


class RoundCreate(RoundBase):
    game_id: UUID4


class Round(RoundBase):
    uuid: UUID4
    game_id: UUID4
    scores: List[Score] = []
    created_at: datetime

    class Config:
        from_attributes = True


class GameAnalytics(BaseModel):
    game_id: UUID4
    current_round: int
    players: List[Player]
    leader: Optional[Player] = None
    points_to_win: List[dict]  # [{"player_name": str, "points_needed": int}, ...]