from fastapi import APIRouter
from api.v1.endpoint import auth, dashboard, goals,groups,leaderboard,quiz,resources,stats


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(groups.router)
api_router.include_router(goals.router)
api_router.include_router(dashboard.router)
api_router.include_router(leaderboard.router)
api_router.include_router(quiz.router)
api_router.include_router(resources.router)
api_router.include_router(stats.router)