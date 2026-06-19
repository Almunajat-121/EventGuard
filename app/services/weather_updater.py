import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.event import Event
from app.models.weather_log import WeatherLog
from app.models.risk_analysis import RiskAnalysis
from app.models.notification import Notification
from app.services.openweather_service import fetch_weather_data
from app.services.risk_engine import process_worst_case_scenario, calculate_risk
from app.services.recommendation_engine import generate_recommendation
from app.database import async_session

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def update_event_weather(event_id: str, db: AsyncSession = None):
    """
    Core function to fetch weather, analyze risk, and trigger notifications.
    Can be called with an existing DB session or it will create its own safely.
    """
    if db is not None:
        return await _do_update_event_weather(event_id, db)
        
    async with async_session() as session:
        try:
            result = await _do_update_event_weather(event_id, session)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating weather for event {event_id}: {e}")
            return False

async def _do_update_event_weather(event_id: str, db: AsyncSession):
    # Get event
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event or event.forecast_status != "AVAILABLE":
        return False
        
    # Get previous risk BEFORE fetching new data (to prevent autoflush issues)
    prev_risk_res = await db.execute(
        select(RiskAnalysis)
        .where(RiskAnalysis.event_id == event_id)
        .order_by(RiskAnalysis.analyzed_at.desc())
        .limit(1)
    )
    prev_risk = prev_risk_res.scalar_one_or_none()
    
    # Fetch Data
    raw_weather = await fetch_weather_data(event.latitude or -6.2088, event.longitude or 106.8456)
    worst_case = process_worst_case_scenario(raw_weather, event.start_date, event.start_time, event.end_time)
    
    if not worst_case:
        return False
        
    # Create Weather Log
    log = WeatherLog(
        event_id=event.id,
        temperature=worst_case["temperature"],
        humidity=worst_case["humidity"],
        wind_speed=worst_case["wind_speed"],
        cloud_coverage=worst_case["cloud_coverage"],
        rain_probability=worst_case["rain_probability"],
        worst_case_time=worst_case["worst_case_time"],
        source_env=settings.openweather_mode
    )
    db.add(log)
    
    # Calculate Risk
    rain_r, wind_r, heat_r, overall_r = calculate_risk(
        worst_case["rain_probability"], 
        worst_case["wind_speed"], 
        worst_case["temperature"]
    )
    
    rec = generate_recommendation(rain_r, wind_r, heat_r, overall_r, worst_case["worst_case_time"])
    
    # Create Risk Analysis Log
    risk = RiskAnalysis(
        event_id=event.id,
        rain_risk=rain_r,
        wind_risk=wind_r,
        heat_risk=heat_r,
        overall_risk=overall_r,
        recommendation=rec
    )
    db.add(risk)
    
    # Notification logic: only notify if it escalated to HIGH
    if overall_r == "HIGH":
        if not prev_risk or prev_risk.overall_risk != "HIGH":
            notif = Notification(
                user_id=event.user_id,
                event_id=event.id,
                type="RISK_ALERT",
                message=f"Peringatan! Risiko cuaca untuk acara '{event.name}' meningkat menjadi HIGH."
            )
            db.add(notif)
            
    return True

async def reanalyze_event_risk(event_id: str, db: AsyncSession = None):
    """
    Re-analyzes risk based on the latest weather data without fetching new data.
    """
    if db is not None:
        return await _do_reanalyze(event_id, db)
    async with async_session() as session:
        try:
            result = await _do_reanalyze(event_id, session)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Error reanalyzing risk for event {event_id}: {e}")
            return False

async def _do_reanalyze(event_id: str, db: AsyncSession):
    # Get event
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event: return False
    
    # Get latest weather
    log_res = await db.execute(
        select(WeatherLog).where(WeatherLog.event_id == event_id).order_by(WeatherLog.fetched_at.desc()).limit(1)
    )
    weather = log_res.scalar_one_or_none()
    if not weather: return False
    
    rain_r, wind_r, heat_r, overall_r = calculate_risk(weather.rain_probability, weather.wind_speed, weather.temperature)
    rec = generate_recommendation(rain_r, wind_r, heat_r, overall_r, weather.worst_case_time)
    
    risk = RiskAnalysis(
        event_id=event.id,
        rain_risk=rain_r, wind_risk=wind_r, heat_risk=heat_r,
        overall_risk=overall_r, recommendation=rec
    )
    db.add(risk)
    return True

async def auto_fetch_weather_task(event_id: str):
    """Background task wrapper"""
    await update_event_weather(event_id)
