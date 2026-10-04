"""
API router for Alerts and Anomaly telemetry (BON-04).
"""

from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import Alert
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
) -> dict:
    """Mark an alert as acknowledged / resolved."""
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "alert_not_found", "message": f"Alert ID {alert_id} not found"},
        )
    alert.resolved_at = datetime.datetime.now(datetime.UTC)
    await session.commit()
    return {"message": "Alert marked as resolved", "alert_id": alert_id}
