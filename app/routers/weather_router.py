from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.core.deps import get_current_user_from_cookie
from app.services.weather_updater import update_event_weather, reanalyze_event_risk

router = APIRouter(prefix="/api/events/{event_id}", tags=["weather", "risk"])

@router.post("/weather/refresh")
async def refresh_weather(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if event.forecast_status == "TOO_FAR":
        raise HTTPException(status_code=400, detail="Event is too far in the future. Forecast unavailable.")
        
    success = await update_event_weather(event_id, db)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update weather. No overlap found or external API error.")
        
    return {"message": "Weather refreshed and risk updated"}

@router.get("/weather", response_model=dict)
async def get_latest_weather(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    # Verify event
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")
        
    from app.models.weather_log import WeatherLog
    log_res = await db.execute(
        select(WeatherLog)
        .where(WeatherLog.event_id == event_id)
        .order_by(WeatherLog.fetched_at.desc())
        .limit(1)
    )
    weather = log_res.scalar_one_or_none()
    if not weather:
        raise HTTPException(status_code=404, detail="Weather data not found")
        
    return {
        "temperature": weather.temperature,
        "humidity": weather.humidity,
        "wind_speed": weather.wind_speed,
        "cloud_coverage": weather.cloud_coverage,
        "rain_probability": weather.rain_probability,
        "worst_case_time": str(weather.worst_case_time) if weather.worst_case_time else None,
        "fetched_at": str(weather.fetched_at)
    }

@router.get("/weather/history", response_model=list[dict])
async def get_weather_history(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")
        
    from app.models.weather_log import WeatherLog
    log_res = await db.execute(
        select(WeatherLog)
        .where(WeatherLog.event_id == event_id)
        .order_by(WeatherLog.fetched_at.desc())
        .limit(10)
    )
    history = log_res.scalars().all()
    return [{"id": h.id, "temp": h.temperature, "rain": h.rain_probability, "fetched_at": str(h.fetched_at)} for h in history]

@router.get("/risk", response_model=dict)
async def get_risk_analysis(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")
        
    from app.models.risk_analysis import RiskAnalysis
    risk_res = await db.execute(
        select(RiskAnalysis)
        .where(RiskAnalysis.event_id == event_id)
        .order_by(RiskAnalysis.analyzed_at.desc())
        .limit(1)
    )
    risk = risk_res.scalar_one_or_none()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk analysis not found")
        
    return {
        "overall_risk": risk.overall_risk,
        "rain_risk": risk.rain_risk,
        "wind_risk": risk.wind_risk,
        "heat_risk": risk.heat_risk,
        "recommendation": risk.recommendation,
        "analyzed_at": str(risk.analyzed_at)
    }

@router.post("/risk/analyze")
async def manual_risk_analyze(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")
        
    success = await reanalyze_event_risk(event_id, db)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reanalyze risk. Make sure weather data exists.")
        
    return {"message": "Risk reanalyzed successfully"}
