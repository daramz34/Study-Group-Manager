from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from crud import get_dashboard
from schemas import DashboardResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from database import get_db
from models import User
from core.dependencies import get_current_user
from services.cache import invalidate_cache, get_cached, set_cache

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/dashboard", tags=["DASHBOARD"])



@router.get("/users/me", response_model=DashboardResponse)
@limiter.limit("3/minute")
def get_dashboard_endpoint(request:Request, db:Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    cache_key = f"dashboard:{current_user.id}"

    
    cached = get_cached(cache_key)
    if cached:
        return cached

    dashboard = get_dashboard(db, current_user)

    
    set_cache(cache_key, dashboard, ttl_seconds=120)

    return dashboard