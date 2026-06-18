from pydantic import BaseModel
from datetime import datetime, time

class WeatherLogResponse(BaseModel):
    id: str
    event_id: str
    temperature: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    cloud_coverage: float | None = None
    rain_probability: float | None = None
    worst_case_time: time | None = None
    fetched_at: datetime

    model_config = {"from_attributes": True}

class RiskAnalysisResponse(BaseModel):
    id: str
    event_id: str
    rain_risk: str
    wind_risk: str
    heat_risk: str
    overall_risk: str
    recommendation: str | None = None
    analyzed_at: datetime

    model_config = {"from_attributes": True}
