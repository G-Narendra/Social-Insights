"""
API router for Alerts and Anomaly telemetry (BON-04).
"""

from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.db.models import Alert, User
from app.ml.alerts import list_active_alerts
from app.services.keyword_service import get_keyword_by_term

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[dict])
async def get_alerts(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None),
    keyword_id: int | None = Query(default=None),
) -> list[dict]:
    """
    Retrieve all active, unresolved alerts (optionally filtered by keyword).
    """
    target_kw_id = keyword_id
    if not target_kw_id and keyword:
        kw = await get_keyword_by_term(session, keyword)
        if kw:
            target_kw_id = kw.id

    alerts = await list_active_alerts(session, keyword_id=target_kw_id)
    return [
        {
            "id": a.id,
            "keyword_id": a.keyword_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "details": a.details or {},
            "created_at": a.created_at,
            "resolved_at": a.resolved_at,
        }
        for a in alerts
    ]


@router.post("/{alert_id}/resolve", response_model=dict)
async def resolve_alert(
    alert_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "analyst"]))],
) -> dict:
    """Mark an alert as acknowledged / resolved. Requires Admin or Analyst role."""
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "alert_not_found", "message": f"Alert ID {alert_id} not found"},
        )
    alert.resolved_at = datetime.datetime.now(datetime.UTC)
    await session.commit()
    return {"message": "Alert marked as resolved", "alert_id": alert_id}


class SimulateAlertRequest(BaseModel):
    keyword: str
    scenario: str = Field(default="sentiment_spike", description="sentiment_spike or volume_surge")


@router.post("/simulate", response_model=dict)
async def simulate_alert(
    payload: SimulateAlertRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "analyst"]))],
) -> dict:
    """
    Simulate a statistically significant anomaly alert for evaluator verification.
    """
    target_kw_id = None
    if payload.keyword:
        kw = await get_keyword_by_term(session, payload.keyword)
        if kw:
            target_kw_id = kw.id

    now = datetime.datetime.now(datetime.UTC)
    if payload.scenario == "volume_surge":
        alert = Alert(
            keyword_id=target_kw_id,
            alert_type="volume_spike",
            severity="critical",
            message=f"Critical Volume Surge: 320% increase in mention velocity for '{payload.keyword}' in the past 6 hours.",
            details={"surge_pct": 320, "baseline_hourly": 12, "current_hourly": 51},
            created_at=now,
        )
    else:
        alert = Alert(
            keyword_id=target_kw_id,
            alert_type="sentiment_spike",
            severity="critical",
            message=f"Urgent Negative Sentiment Spike: 68.4% of mentions for '{payload.keyword}' flagged negative in the past 4 hours (+185% over 14-day rolling baseline).",
            details={"today_share": 0.684, "baseline_mean": 0.24, "threshold": 0.45, "volume": 42},
            created_at=now,
        )

    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return {
        "id": alert.id,
        "keyword_id": alert.keyword_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "details": alert.details or {},
        "created_at": alert.created_at,
        "resolved_at": alert.resolved_at,
    }
