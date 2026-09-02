from fastapi import APIRouter, HTTPException, status, Depends, Request
from crud import start_quiz, submit_quiz
from schemas import QuizResponse, SubmitAnswers
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from database import get_db
from models import User
from core.dependencies import get_current_user



limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/quiz", tags=["QUIZZES"])



@router.post("/goals/{goal_id}/start-quiz", response_class=QuizResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/day")
async def start_quiz_endpoint(request: Request, goal_id: int, db:Session = Depends(get_current_user), current_user:User = Depends(get_current_user)):
    db_quiz = await start_quiz(db, goal_id, current_user)

    if not db_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or quiz already started today"
        )

    return db_quiz

@router.post("/{quiz_id}/submit", response_model=QuizResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/day")
async def submit_quiz_endpoint(
    request: Request,
    quiz_id: int,
    body: SubmitAnswers,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_quiz, error = await submit_quiz(db, quiz_id, body.answers, current_user)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    return db_quiz

