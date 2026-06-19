from fastapi import FastAPI
from app.config import get_settings
from app.routers import auth_router, event_router, weather_router, dashboard_router, notifications_router

settings = get_settings()

from contextlib import asynccontextmanager
from app.services.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(
    title="EventGuard",
    description="SaaS Weather Risk Monitoring for Outdoor Events",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth_router.router)
app.include_router(event_router.router)
app.include_router(weather_router.router)
app.include_router(dashboard_router.router)
app.include_router(notifications_router.router)

from app.routers import landing_router
app.include_router(landing_router.router)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.app_env,
        "weather_mode": settings.openweather_mode
    }
