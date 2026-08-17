from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..database import get_db
from ..auth import require_roles, get_current_user

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

ADMIN_ONLY = ["admin"]


@router.get("/dashboard", response_model=schemas.AdminDashboard)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ADMIN_ONLY)),
):
    total_users = db.query(models.User).count()

    users_by_role_raw = (
        db.query(models.User.role, func.count(models.User.id))
        .group_by(models.User.role)
        .all()
    )
    users_by_role = [schemas.RoleCount(role=role.value, count=count) for role, count in users_by_role_raw]

    logins_by_role_raw = (
        db.query(models.User.role, func.coalesce(func.sum(models.User.login_count), 0))
        .group_by(models.User.role)
        .all()
    )
    logins_by_role = [schemas.RoleCount(role=role.value, count=int(count)) for role, count in logins_by_role_raw]
    total_logins = sum(rc.count for rc in logins_by_role)

    active_users = db.query(models.User).filter(models.User.is_active == True).count()  # noqa: E712
    inactive_users = total_users - active_users

    total_athletes = db.query(models.Athlete).count()
    total_videos = db.query(models.Video).count()

    videos_by_status_raw = (
        db.query(models.Video.status, func.count(models.Video.id))
        .group_by(models.Video.status)
        .all()
    )
    videos_by_status = [schemas.StatusCount(status=s.value, count=c) for s, c in videos_by_status_raw]

    total_processed_reports = db.query(models.BiomechanicsReport).count()

    avg_quality = db.query(func.avg(models.BiomechanicsReport.movement_quality_score)).scalar()
    avg_quality = round(avg_quality, 1) if avg_quality is not None else None

    high_risk_video_count = (
        db.query(models.BiomechanicsReport)
        .filter(models.BiomechanicsReport.risk_category.in_(["High", "Critical"]))
        .count()
    )

    recent_users = (
        db.query(models.User)
        .order_by(models.User.created_at.desc())
        .limit(5)
        .all()
    )

    return schemas.AdminDashboard(
        total_users=total_users,
        users_by_role=users_by_role,
        total_logins=total_logins,
        logins_by_role=logins_by_role,
        active_users=active_users,
        inactive_users=inactive_users,
        total_athletes=total_athletes,
        total_videos=total_videos,
        videos_by_status=videos_by_status,
        total_processed_reports=total_processed_reports,
        avg_platform_movement_quality=avg_quality,
        high_risk_video_count=high_risk_video_count,
        recent_users=[
            schemas.RecentUser(
                id=u.id, full_name=u.full_name, email=u.email,
                role=u.role, created_at=u.created_at,
            ) for u in recent_users
        ],
    )


@router.get("/users", response_model=List[schemas.UserAdminOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ADMIN_ONLY)),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.put("/users/{user_id}/toggle-active", response_model=schemas.UserAdminOut)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(ADMIN_ONLY)),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't deactivate your own account")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user
