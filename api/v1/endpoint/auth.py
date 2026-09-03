from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from schemas import UserCreate, UserResponse, TokenResponse
from crud import create_user, authenticate_user, get_user_by_email, get_user_by_username
from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from core.security import create_access_token
from services.email import welcome_email
from fastapi.security import OAuth2PasswordRequestForm

router  = APIRouter(prefix="/auth", tags=["AUTH"])
limiter = Limiter(key_func=get_remote_address)



@router.post("/register", response_model=UserResponse, description="User Register")
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate, db:Session=Depends(get_db)):
    existing_user = get_user_by_username(db, user.username)
    existing_email = get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "Username is already registered"
        )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    db_user = create_user(db, user)


    welcome_email(to=user.email, username=user.username)

    return db_user


@router.post("/login", response_model=TokenResponse, description="User Login")
@limiter.limit("10/hour")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session=Depends(get_db)):
    user = authenticate_user(db, form.username, form.password)

    if not user:
        raise HTTPException(
            status_code =401,
            detail="Invalid Username or password"

        )

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer"
    }



