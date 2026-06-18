import uuid
from datetime import datetime, timezone, date, time
from sqlalchemy import String, DateTime, Date, Time, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    forecast_status: Mapped[str] = mapped_column(String(20), default="TOO_FAR")
    status: Mapped[str] = mapped_column(String(20), default="upcoming")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="events")
    weather_logs: Mapped[list["WeatherLog"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    risk_analyses: Mapped[list["RiskAnalysis"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="event", cascade="all, delete-orphan")
