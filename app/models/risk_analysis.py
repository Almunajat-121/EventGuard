import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class RiskAnalysis(Base):
    __tablename__ = "risk_analysis"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    
    rain_risk: Mapped[str] = mapped_column(String(10), default="PENDING")
    wind_risk: Mapped[str] = mapped_column(String(10), default="PENDING")
    heat_risk: Mapped[str] = mapped_column(String(10), default="PENDING")
    overall_risk: Mapped[str] = mapped_column(String(10), default="PENDING")
    
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event: Mapped["Event"] = relationship(back_populates="risk_analyses")
