from pydantic import BaseModel
from datetime import date, time, datetime

class EventCreate(BaseModel):
    name: str
    location: str
    timezone: str = "Asia/Jakarta"
    start_date: date
    end_date: date
    start_time: time
    end_time: time

class EventUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None

class EventResponse(BaseModel):
    id: str
    user_id: str
    name: str
    location: str
    latitude: float | None = None
    longitude: float | None = None
    timezone: str
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    forecast_status: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
