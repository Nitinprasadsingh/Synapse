from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_analyst, require_operator
from app.models.user import User
from app.models.alert import SystemAlert
from app.schemas.alert import SystemAlertSchema, SystemAlertCreate

router = APIRouter()


@router.get("", response_model=List[SystemAlertSchema])
def list_alerts(
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_acknowledged: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    List alerts with optional filtering by category, severity, and acknowledgment status.
    """
    query = db.query(SystemAlert)
    if category:
        query = query.filter(SystemAlert.category == category)
    if severity:
        query = query.filter(SystemAlert.severity == severity)
    if is_acknowledged is not None:
        query = query.filter(SystemAlert.is_acknowledged == is_acknowledged)

    alerts = query.order_by(SystemAlert.timestamp.desc()).all()
    return alerts


@router.post("", response_model=SystemAlertSchema)
def create_alert(
    alert_in: SystemAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Create a new operational alert.
    """
    alert = SystemAlert(
        title=alert_in.title,
        message=alert_in.message,
        category=alert_in.category,
        severity=alert_in.severity,
        is_acknowledged=False,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/{alert_id}/acknowledge", response_model=SystemAlertSchema)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Mark an active system alert as acknowledged by the operator/admin.
    """
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )

    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledged_by = current_user.email
    db.commit()
    db.refresh(alert)
    return alert
