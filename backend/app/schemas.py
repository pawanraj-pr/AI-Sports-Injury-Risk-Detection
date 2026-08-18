from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import (
    RoleEnum, VideoStatusEnum, ActivityTypeEnum,
    InjurySeverityEnum, TrainingLoadLevelEnum,
)


# ---------- Auth / User ----------

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.athlete


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    is_active: bool
    login_count: int
    last_login_at: Optional[datetime] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Athlete ----------

class AthleteBase(BaseModel):
    athlete_code: str
    sport_type: str
    position: Optional[str] = None
    age: int
    height_cm: float
    weight_kg: float
    injury_history: Optional[str] = None
    training_load: Optional[str] = None
    injury_severity: InjurySeverityEnum = InjurySeverityEnum.none
    training_load_level: TrainingLoadLevelEnum = TrainingLoadLevelEnum.moderate


class AthleteCreate(AthleteBase):
    user_id: Optional[int] = None


class AthleteSelfCreate(AthleteBase):
    """Used when an athlete creates their OWN profile — user_id is set
    server-side from the logged-in account, never client-supplied."""
    pass


class AthleteUpdate(BaseModel):
    sport_type: Optional[str] = None
    position: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    injury_history: Optional[str] = None
    training_load: Optional[str] = None
    injury_severity: Optional[InjurySeverityEnum] = None
    training_load_level: Optional[TrainingLoadLevelEnum] = None


class AthleteOut(AthleteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# ---------- Video / Pose / Biomechanics (Milestone 2) ----------

class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    activity_type: ActivityTypeEnum
    filename: str
    status: VideoStatusEnum
    duration_seconds: Optional[float]
    frames_processed: Optional[int]
    error_message: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]


class BiomechanicsReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    avg_left_knee_angle: Optional[float]
    avg_right_knee_angle: Optional[float]
    knee_valgus_score: Optional[float]
    hip_stability_score: Optional[float]
    trunk_lean_degrees: Optional[float]
    landing_mechanics_score: Optional[float]
    stride_length_ratio: Optional[float]
    joint_alignment_score: Optional[float]
    balance_score: Optional[float]
    movement_symmetry_score: Optional[float]
    movement_quality_score: Optional[float]
    risk_category: Optional[str]
    notes: Optional[str]
    created_at: datetime


class VideoWithReportOut(VideoOut):
    report: Optional[BiomechanicsReportOut] = None


# ---------- Combined / Summary Reports ----------

class VideoSummaryEntry(BaseModel):
    video_id: int
    filename: str
    activity_type: ActivityTypeEnum
    movement_quality_score: Optional[float]
    risk_category: Optional[str]
    uploaded_at: datetime


class AthleteReportSummary(BaseModel):
    athlete_id: int
    video_count: int
    avg_movement_quality_score: Optional[float] = None
    avg_hip_stability_score: Optional[float] = None
    avg_landing_mechanics_score: Optional[float] = None
    avg_joint_alignment_score: Optional[float] = None
    avg_balance_score: Optional[float] = None
    avg_movement_symmetry_score: Optional[float] = None
    avg_knee_valgus_score: Optional[float] = None
    videos: List[VideoSummaryEntry] = []
    message: Optional[str] = None


# ---------- Injury Risk Prediction (Milestone 3) ----------

class RiskComponent(BaseModel):
    label: str
    weight_pct: int
    score: float          # 0-100, higher = more risk contribution
    category: str          # Low / Moderate / High / Critical


class InjuryCategoryRisk(BaseModel):
    name: str
    score: float           # 0-100, elevated-risk indicator, NOT a clinical probability
    category: str
    note: Optional[str] = None


class MovementAnomaly(BaseModel):
    video_id: int
    filename: str
    description: str


class Recommendation(BaseModel):
    category: str           # Exercise / Mobility / Strengthening / Recovery / Training Modification
    text: str


class AthleteRiskAssessment(BaseModel):
    athlete_id: int
    video_count: int
    overall_score: Optional[float] = None
    overall_category: Optional[str] = None
    components: List[RiskComponent] = []
    injury_categories: List[InjuryCategoryRisk] = []
    anomalies: List[MovementAnomaly] = []
    recommendations: List[Recommendation] = []
    message: Optional[str] = None
    generated_at: datetime


# ---------- Admin Dashboard / Executive Analytics (Milestone 4) ----------

class RoleCount(BaseModel):
    role: str
    count: int


class StatusCount(BaseModel):
    status: str
    count: int


class RecentUser(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    created_at: datetime


class AdminDashboard(BaseModel):
    total_users: int
    users_by_role: List[RoleCount]
    total_logins: int
    logins_by_role: List[RoleCount]
    active_users: int
    inactive_users: int
    total_athletes: int
    total_videos: int
    videos_by_status: List[StatusCount]
    total_processed_reports: int
    avg_platform_movement_quality: Optional[float] = None
    high_risk_video_count: int
    recent_users: List[RecentUser] = []


class UserAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    is_active: bool
    login_count: int
    last_login_at: Optional[datetime] = None
    created_at: datetime


# ---------- Team Overview (Coach / Physiotherapist / Admin) ----------

class TeamOverviewEntry(BaseModel):
    athlete_id: int
    athlete_code: str
    sport_type: str
    injury_severity: InjurySeverityEnum
    training_load_level: TrainingLoadLevelEnum
    video_count: int
    latest_movement_quality_score: Optional[float] = None
    latest_risk_category: Optional[str] = None
    needs_attention: bool
