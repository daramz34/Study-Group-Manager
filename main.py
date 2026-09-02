from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from api.v1.router import api_router
from database import engine, Base
from services.scheduler import start_scheduler, shutdown_scheduler
from core.config import settings



# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# Lifespan — startup & shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    print("✅ Server started, scheduler running")
    yield
    # Shutdown
    shutdown_scheduler()
    print("🛑 Scheduler stopped")


app = FastAPI(
    title=settings.APP_NAME, 
    description="Learn Together, Rank Together",
    version=settings.VERSION,
    lifespan=lifespan
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific URLs in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to StudyGroup API", "docs": "/docs"}




