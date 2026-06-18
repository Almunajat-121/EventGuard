from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date, timezone
from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.event_schema import EventCreate, EventUpdate, EventResponse
from app.core.deps import get_current_user_from_cookie
from app.services.openweather_service import geocode_location
from app.services.weather_updater import auto_fetch_weather_task
from fastapi import BackgroundTasks

router = APIRouter(prefix="/api/events", tags=["events"])

@router.post("", response_model=EventResponse)
async def create_event(
    event_data: EventCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    # Cek kuota event berdasarkan tier (Mock Logic)
    if current_user.subscription_tier == "free":
        result = await db.execute(select(Event).where(Event.user_id == current_user.id))
        if len(result.scalars().all()) >= 3:
            raise HTTPException(status_code=403, detail="Free tier limit reached (3 events). Please upgrade to Pro.")

    # Geocoding
    coords = await geocode_location(event_data.location)
    lat, lon = None, None
    if coords:
        lat, lon = coords["lat"], coords["lon"]

    # Logika TOO_FAR vs AVAILABLE
    today = datetime.now(timezone.utc).date()
    days_difference = (event_data.start_date - today).days
    
    forecast_status = "AVAILABLE" if days_difference <= 5 else "TOO_FAR"
    if days_difference < 0:
        forecast_status = "PASSED"

    new_event = Event(
        user_id=current_user.id,
        name=event_data.name,
        location=event_data.location,
        latitude=lat,
        longitude=lon,
        timezone=event_data.timezone,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        forecast_status=forecast_status
    )
    
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    
    # Panggil BackgroundTasks untuk initial fetch cuaca jika AVAILABLE
    if forecast_status == "AVAILABLE":
        background_tasks.add_task(auto_fetch_weather_task, new_event.id)
    
    return new_event

@router.get("", response_model=list[EventResponse])
async def list_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.user_id == current_user.id))
    return result.scalars().all()

from app.models.weather_log import WeatherLog
from app.models.risk_analysis import RiskAnalysis

@router.get("/{event_id}/details")
async def get_event_details(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    # Get Event
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Get Latest Weather Log
    log_res = await db.execute(
        select(WeatherLog)
        .where(WeatherLog.event_id == event_id)
        .order_by(WeatherLog.fetched_at.desc())
        .limit(1)
    )
    weather = log_res.scalar_one_or_none()
    
    # Get Latest Risk Analysis
    risk_res = await db.execute(
        select(RiskAnalysis)
        .where(RiskAnalysis.event_id == event_id)
        .order_by(RiskAnalysis.analyzed_at.desc())
        .limit(1)
    )
    risk = risk_res.scalar_one_or_none()
    
    return {
        "event": {
            "name": event.name,
            "location": event.location,
            "start_date": str(event.start_date),
            "start_time": str(event.start_time),
            "end_time": str(event.end_time)
        },
        "weather": {
            "temperature": weather.temperature if weather else None,
            "rain_probability": weather.rain_probability if weather else None,
            "wind_speed": weather.wind_speed if weather else None
        } if weather else None,
        "risk": {
            "overall_risk": risk.overall_risk if risk else None,
            "recommendation": risk.recommendation if risk else None
        } if risk else None
    }

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    update_data = event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
        
    await db.commit()
    await db.refresh(event)
    return event

@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == current_user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted successfully"}
