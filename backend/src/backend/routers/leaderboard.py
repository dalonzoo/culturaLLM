from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from backend.services.database import get_db
from backend.models.schemas import User, LeaderboardEntry

router = APIRouter()

@router.get("/", response_model=List[LeaderboardEntry])
async def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).order_by(desc(User.score)).limit(limit).all()
    
    leaderboard = []
    for rank, user in enumerate(users, 1):
        leaderboard.append(LeaderboardEntry(
            username=user.username,
            score=user.score,
            badges=user.badges,
            rank=rank
        ))
    
    return leaderboard
