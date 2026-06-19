import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime, timezone
from app.database import async_session
from app.models.event import Event
from app.services.weather_updater import update_event_weather

logger = logging.getLogger(__name__)

async def update_event_statuses():
    """Update event status based on current date"""
    async with async_session() as db:
        try:
            today = datetime.now(timezone.utc).date()
            
            # Get all events
            result = await db.execute(select(Event))
            events = result.scalars().all()
            
            for event in events:
                days_diff = (event.start_date - today).days
                
                # Update forecast status
                if days_diff <= 5 and days_diff >= 0:
                    event.forecast_status = "AVAILABLE"
                elif days_diff > 5:
                    event.forecast_status = "TOO_FAR"
                else:
                    event.forecast_status = "PASSED"
                    
                # Update general status
                if event.end_date < today:
                    event.status = "done"
                elif event.start_date <= today <= event.end_date:
                    event.status = "active"
                else:
                    event.status = "upcoming"
                    
            await db.commit()
        except Exception as e:
            logger.error(f"Error updating event statuses: {e}")
            await db.rollback()

async def auto_fetch_weather_all():
    """Fetch weather for all AVAILABLE events"""
    async with async_session() as db:
        try:
            result = await db.execute(select(Event).where(Event.forecast_status == "AVAILABLE"))
            events = result.scalars().all()
            
            for event in events:
                await update_event_weather(event.id, db)
        except Exception as e:
            logger.error(f"Error auto fetching weather: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Run status update every hour
    scheduler.add_job(update_event_statuses, "interval", hours=1)
    # Run weather fetch every 3 hours (OpenWeatherMap free tier friendly)
    scheduler.add_job(auto_fetch_weather_all, "interval", hours=3)
    scheduler.start()
    logger.info("APScheduler started")
