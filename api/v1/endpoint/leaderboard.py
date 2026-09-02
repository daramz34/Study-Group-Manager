from fastapi import APIRouter, HTTPException, status, Depends, Request
from crud import get_group_leaderboard
from schemas import LeaderboardEntry, LeaderboardResponse
from database import get_db
from core.dependencies import get_current_user
from models import User
from sqlalchemy.orm import Session
from services.cache import invalidate_cache, get_cached, set_cache


router = APIRouter(prefix=("/leaderboard"), tags=["LEADERBOARD"])


@router.get("/groups/{group_id}", response_model=list[LeaderboardResponse], status_code=200)
def get_leaderboard(group_id: int, week: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cache_key = f"leaderboard:{group_id}:{week}"

    # Check cache first
    cached = get_cached(cache_key)
    if cached:
        return cached

    entries = get_group_leaderboard(db, group_id, week)
    
    if entries is None:
        raise HTTPException(
            status_code=404,
            detail="Group not found or you are not a member"
        )

    result = {
        "group_id": group_id,
        "week_number": week or 0,
        "entries": entries
    }

    # Cache for 5 minutes
    set_cache(cache_key, result, ttl_seconds=300)

    return result