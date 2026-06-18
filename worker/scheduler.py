import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import logging

from app.database import async_session
from app.models.event import Event
from app.models.weather_log import WeatherLog
from app.models.risk_analysis import RiskAnalysis
from app.models.notification import Notification
from app.services.openweather_service import fetch_weather_data
from app.services.risk_engine import process_worst_case_scenario, calculate_risk
from app.services.recommendation_engine import generate_recommendation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_events():
    logger.info(f"[{datetime.now()}] Starting background event processing...")
    async with async_session() as db:
        # Get active/upcoming events
        result = await db.execute(select(Event).where(Event.status.in_(["upcoming", "active"])))
        events = result.scalars().all()
        
        today = datetime.now(timezone.utc).date()
        
        for event in events:
            days_difference = (event.start_date - today).days
            
            # Update forecast status
            if days_difference < 0:
                event.forecast_status = "PASSED"
                event.status = "done"
                continue
            elif days_difference <= 5:
                event.forecast_status = "AVAILABLE"
            else:
                event.forecast_status = "TOO_FAR"
                
            if event.forecast_status == "AVAILABLE":
                from app.services.weather_updater import update_event_weather
                success = await update_event_weather(event.id, db)
                if not success:
                    logger.error(f"Failed to update weather for event {event.id}")

        await db.commit()
    logger.info("Finished background processing.")

if __name__ == "__main__":
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_events, 'interval', hours=6)
    logger.info("Scheduler started. Running every 6 hours.")
    scheduler.start()
    
    # Run forever
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
