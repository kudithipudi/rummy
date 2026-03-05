from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pass


class User(UserBase):
    uuid: UUID
    created_at: datetime
    is_active: bool = True

    @field_validator('is_active', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, int):
            return bool(v)
        return v

    class Config:
        from_attributes = True


class PlayerBase(BaseModel):
    name: str


class PlayerCreate(PlayerBase):
    game_id: UUID


class Player(PlayerBase):
    uuid: UUID
    game_id: UUID
    total_score: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class GameBase(BaseModel):
    score_cutoff: int  # 100, 150, or 201


class GameCreate(GameBase):
    player_names: List[str]


class Game(GameBase):
    uuid: UUID
    created_by: UUID
    is_completed: bool = False
    is_cancelled: bool = False
    winner_id: Optional[UUID] = None
    created_at: datetime
    players: List[Player] = []

    @field_validator('is_completed', 'is_cancelled', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, int):
            return bool(v)
        return v

    class Config:
        from_attributes = True


class ScoreBase(BaseModel):
    points: int


class ScoreCreate(ScoreBase):
    player_id: UUID
    round_id: UUID


class Score(ScoreBase):
    uuid: UUID
    player_id: UUID
    round_id: UUID
    cumulative_total: int
    created_at: datetime

    class Config:
        from_attributes = True


class RoundBase(BaseModel):
    round_number: int


class RoundCreate(RoundBase):
    game_id: UUID


class Round(RoundBase):
    uuid: UUID
    game_id: UUID
    scores: List[Score] = []
    created_at: datetime

    class Config:
        from_attributes = True


class GameAnalytics(BaseModel):
    game_id: UUID
    current_round: int
    players: List[Player]
    leader: Optional[Player] = None
    points_to_win: List[dict]  # [{"player_name": str, "points_needed": int}, ...]
