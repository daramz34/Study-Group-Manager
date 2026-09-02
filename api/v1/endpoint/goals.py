from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from crud import (create_goal, get_group_goals, get_goal_by_id, update_goal, delete_goal)
from schemas import GoalCreate, GoalResponse, GoalUpdate, GoalCompletionResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from database import get_db
from models import User
from core.dependencies import get_current_user


limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/goals", tags=["GOALS"])



@router.post("/group/{group_id}", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/day")
def create_goal_endpoint(request: Request, group_id:int, goal: GoalCreate, db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    db_goal = create_goal(db, group_id, goal, current_user)

    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a group member"
        )

    return db_goal



@router.get("/group/{group_id}", response_model=list[GoalResponse], status_code=status.HTTP_200_OK)
def list_goals_endpoint(group_id: int, db:Session=Depends(get_db), current_user: User = Depends(get_current_user)):
    db_goals = get_group_goals(db, group_id, current_user)
    if  db_goals is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a group member"
        )
    return db_goals

@router.get("/{goal_id}", response_model=GoalResponse, status_code=status.HTTP_200_OK)
def get_goals_by_id_endpoint(goal_id: int, db:Session=Depends(get_db), current_user: User = Depends(get_current_user)):
    db_goals = get_goal_by_id(db, goal_id, current_user)
    if not db_goals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No goals found"
        )
    return db_goals

@router.put("/{goal_id}", response_model=GoalResponse, status_code=status.HTTP_200_OK)
def update_goal_endpoint(goal_id: int, goal_update: GoalUpdate, db:Session=Depends(get_db), current_user: User = Depends(get_current_user)):
    db_goals = update_goal(db, goal_id, goal_update, current_user)
    if not db_goals:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin/Owner can update"
        )
    return db_goals

@router.delete("/{goal_id}",  status_code=status.HTTP_204_NO_CONTENT)
def delete_goal_endpoint(goal_id: int, db:Session=Depends(get_db), current_user: User = Depends(get_current_user)):
    db_goals = delete_goal(db, goal_id,  current_user)
    if not db_goals:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin/Owner can delete"
        )
    return Response(status_code=204)
