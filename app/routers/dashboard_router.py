from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.database import get_db
from app.models.event import Event
from app.models.risk_analysis import RiskAnalysis
from app.models.user import User
from app.core.deps import get_current_user_from_cookie

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    # Total Event
    result_total = await db.execute(select(func.count(Event.id)).where(Event.user_id == current_user.id))
    total_events = result_total.scalar() or 0
    
    # Upcoming Event
    today = datetime.now(timezone.utc).date()
    result_upcoming = await db.execute(
        select(func.count(Event.id))
        .where(Event.user_id == current_user.id)
        .where(Event.start_date >= today)
    )
    upcoming_events = result_upcoming.scalar() or 0
    
    # High Risk Event
    # Ambil event id dari risk analysis terbaru yang HIGH
    # (Untuk penyederhanaan, count event yang berelasi dan punya status HIGH terakhir)
    # Di SQLite, ini mungkin butuh subquery. Untuk MVP, ambil dari tabel Event.
    result_high_risk = await db.execute(
        select(func.count(func.distinct(Event.id)))
        .join(RiskAnalysis, Event.id == RiskAnalysis.event_id)
        .where(Event.user_id == current_user.id)
        .where(RiskAnalysis.overall_risk == "HIGH")
    )
    high_risk_events = result_high_risk.scalar() or 0
    
    result_medium = await db.execute(
        select(func.count(func.distinct(Event.id)))
        .join(RiskAnalysis, Event.id == RiskAnalysis.event_id)
        .where(Event.user_id == current_user.id)
        .where(RiskAnalysis.overall_risk == "MEDIUM")
    )
    medium_risk_events = result_medium.scalar() or 0

    result_low = await db.execute(
        select(func.count(func.distinct(Event.id)))
        .join(RiskAnalysis, Event.id == RiskAnalysis.event_id)
        .where(Event.user_id == current_user.id)
        .where(RiskAnalysis.overall_risk == "LOW")
    )
    low_risk_events = result_low.scalar() or 0
    
    return {
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "high_risk_events": high_risk_events,
        "medium_risk_events": medium_risk_events,
        "low_risk_events": low_risk_events,
        "subscription": current_user.subscription_tier
    }
