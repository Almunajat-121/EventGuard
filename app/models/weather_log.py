import uuid
from datetime import datetime, timezone, time
from sqlalchemy import String, DateTime, Time, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class WeatherLog(Base):
    __tablename__ = "weather_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    cloud_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    rain_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    worst_case_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    source_env: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event: Mapped["Event"] = relationship(back_populates="weather_logs")
