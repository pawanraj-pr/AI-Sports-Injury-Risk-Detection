from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, require_roles
from ..report_pdf import build_summary_report_pdf, build_risk_assessment_pdf
from ..risk_engine import build_risk_assessment

router = APIRouter(prefix="/athletes", tags=["Athlete Profile Management"])

# Roles allowed to create/edit/delete athlete records ON BEHALF OF SOMEONE ELSE
MANAGE_ROLES = ["coach", "physiotherapist", "sports_scientist", "admin"]


def _check_access(athlete: models.Athlete, current_user: models.User):
    if current_user.role.value == "athlete" and athlete.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this athlete's data")


# =========================================================
# Self-service endpoints — an athlete managing THEIR OWN profile.
# Declared before the generic "/{athlete_id}" routes so "/me" and
# "/reports/..." are never mistaken for an athlete_id.
# =========================================================

@router.get("/me", response_model=schemas.AthleteOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role.value != "athlete":
        raise HTTPException(status_code=400, detail="Only athlete-role accounts have a self-profile")

    athlete = db.query(models.Athlete).filter(models.Athlete.user_id == current_user.id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="You haven't created your athlete profile yet")
    return athlete


@router.post("/me", response_model=schemas.AthleteOut, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    athlete_in: schemas.AthleteSelfCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role.value != "athlete":
        raise HTTPException(status_code=400, detail="Only athlete-role accounts can create a self-profile")

    existing = db.query(models.Athlete).filter(models.Athlete.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have an athlete profile — use edit instead")

    code_taken = db.query(models.Athlete).filter(
        models.Athlete.athlete_code == athlete_in.athlete_code
    ).first()
    if code_taken:
        raise HTTPException(status_code=400, detail="Athlete code already exists — choose a different one")

    athlete = models.Athlete(user_id=current_user.id, **athlete_in.model_dump())
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return athlete


@router.put("/me", response_model=schemas.AthleteOut)
def update_my_profile(
    athlete_in: schemas.AthleteUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role.value != "athlete":
        raise HTTPException(status_code=400, detail="Only athlete-role accounts have a self-profile")

    athlete = db.query(models.Athlete).filter(models.Athlete.user_id == current_user.id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Create your athlete profile first")

    for field, value in athlete_in.model_dump(exclude_unset=True).items():
        setattr(athlete, field, value)

    db.commit()
    db.refresh(athlete)
    return athlete


# =========================================================
# Combined / summary reports across all of an athlete's videos
# =========================================================

def _completed_reports_for(athlete_id: int, db: Session):
    videos = db.query(models.Video).filter(
        models.Video.athlete_id == athlete_id,
        models.Video.status == models.VideoStatusEnum.completed,
    ).all()
    return [(v, v.report) for v in videos if v.report]


def _avg(reports_with_videos, field):
    vals = [getattr(r, field) for _, r in reports_with_videos if getattr(r, field) is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


@router.get("/{athlete_id}/reports/summary", response_model=schemas.AthleteReportSummary)
def get_reports_summary(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    athlete = db.query(models.Athlete).filter(models.Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    _check_access(athlete, current_user)

    reports = _completed_reports_for(athlete_id, db)
    if not reports:
        return schemas.AthleteReportSummary(
            athlete_id=athlete_id, video_count=0,
            message="No completed video reports yet for this athlete.",
        )

    return schemas.AthleteReportSummary(
        athlete_id=athlete_id,
        video_count=len(reports),
        avg_movement_quality_score=_avg(reports, "movement_quality_score"),
        avg_hip_stability_score=_avg(reports, "hip_stability_score"),
        avg_landing_mechanics_score=_avg(reports, "landing_mechanics_score"),
        avg_joint_alignment_score=_avg(reports, "joint_alignment_score"),
        avg_balance_score=_avg(reports, "balance_score"),
        avg_movement_symmetry_score=_avg(reports, "movement_symmetry_score"),
        avg_knee_valgus_score=_avg(reports, "knee_valgus_score"),
        videos=[
            schemas.VideoSummaryEntry(
                video_id=v.id, filename=v.filename, activity_type=v.activity_type,
                movement_quality_score=r.movement_quality_score,
                risk_category=r.risk_category, uploaded_at=v.uploaded_at,
            )
            for v, r in sorted(reports, key=lambda vr: vr[0].uploaded_at)
        ],
    )


@router.get("/{athlete_id}/reports/summary/pdf")
def download_reports_summary_pdf(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    athlete = db.query(models.Athlete).filter(models.Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    _check_access(athlete, current_user)

    reports = _completed_reports_for(athlete_id, db)
    if not reports:
        raise HTTPException(status_code=400, detail="No completed reports available yet to generate a combined PDF")

    pdf_bytes = build_summary_report_pdf(athlete, reports)
    filename = f"{athlete.athlete_code}_combined_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =========================================================
# Injury Risk Prediction / Movement Anomaly Detection /
# Corrective Recommendations — Milestone 3
# =========================================================

@router.get("/{athlete_id}/risk-assessment", response_model=schemas.AthleteRiskAssessment)
def get_risk_assessment(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    athlete = db.query(models.Athlete).filter(models.Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    _check_access(athlete, current_user)

    reports = _completed_reports_for(athlete_id, db)
    return build_risk_assessment(athlete, reports)


@router.get("/{athlete_id}/risk-assessment/pdf")
def download_risk_assessment_pdf(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    athlete = db.query(models.Athlete).filter(models.Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    _check_access(athlete, current_user)

    reports = _completed_reports_for(athlete_id, db)
    assessment = build_risk_assessment(athlete, reports)
    if assessment["video_count"] == 0:
        raise HTTPException(status_code=400, detail="No completed reports available yet to assess risk")

    pdf_bytes = build_risk_assessment_pdf(athlete, assessment)
    filename = f"{athlete.athlete_code}_risk_assessment.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =========================================================
# Staff-managed athlete CRUD (create/edit/delete on behalf of an athlete)
# =========================================================

@router.post("/", response_model=schemas.AthleteOut, status_code=status.HTTP_201_CREATED)
def create_athlete(
    athlete_in: schemas.AthleteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(MANAGE_ROLES)),
):
    existing = db.query(models.Athlete).filter(
        models.Athlete.athlete_code == athlete_in.athlete_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Athlete code already exists")

    athlete = models.Athlete(**athlete_in.model_dump())
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return athlete


@router.get("/", response_model=List[schemas.AthleteOut])
def list_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Athletes only see their own profile; staff roles see everyone.
    if current_user.role.value == "athlete":
        return db.query(models.Athlete).filter(
            models.Athlete.user_id == current_user.id
        ).all()
    return db.query(models.Athlete).all()


@router.get("/{athlete_id}", response_model=schemas.AthleteOut)
def get_athlete(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    athlete = db.query(models.Athlete).filter(models.Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    _check_access(athlete, current_user)
    return athlete


@router.put("/{athlete_id}", response_model=schemas.AthleteOut)
def update_athlete(
    athlete_id: int,
    athlete_in: schemas.AthleteUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(MANAGE_ROLES)),
):
    athlete = db.query(models.Athlete).filter(models.Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    for field, value in athlete_in.model_dump(exclude_unset=True).items():
        setattr(athlete, field, value)

    db.commit()
    db.refresh(athlete)
    return athlete


@router.delete("/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_athlete(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin"])),
):
    athlete = db.query(models.Athlete).filter(models.Athlete.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    db.delete(athlete)
    db.commit()
    return None
