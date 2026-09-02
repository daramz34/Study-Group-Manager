from fastapi import APIRouter, HTTPException, status, Depends
from crud import get_user_stats
from schemas import UserStatsResponse
from database import get_db
from core.dependencies import get_current_user
from models import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/user_stats", tags=["USER-STATS"])


@router.get("/groups/{group_id}/user/{user_id}", response_model=UserStatsResponse, status_code=status.HTTP_200_OK)
def get_user_stats_endpoint(group_id: int, user_id:int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stats = get_user_stats(db, user_id, group_id, current_user)
    if not stats:
        raise HTTPException(status_code=403, detail="Not a group member")
    return stats



