from datetime import datetime
from typing import List, Tuple

from . import models

# ---------- Weighted overall injury risk model ----------

WEIGHTS = {
    "biomechanical_deviations": 0.35,
    "historical_injury_factors": 0.20,
    "movement_asymmetry": 0.20,
    "training_load": 0.15,
    "fatigue_indicators": 0.10,
}

INJURY_SEVERITY_SCORE = {
    models.InjurySeverityEnum.none: 10,
    models.InjurySeverityEnum.mild: 35,
    models.InjurySeverityEnum.moderate: 65,
    models.InjurySeverityEnum.severe: 90,
}

TRAINING_LOAD_SCORE = {
    models.TrainingLoadLevelEnum.low: 20,
    models.TrainingLoadLevelEnum.moderate: 45,
    models.TrainingLoadLevelEnum.high: 70,
    models.TrainingLoadLevelEnum.very_high: 90,
}

THROWING_ACTIVITIES = {models.ActivityTypeEnum.throwing, models.ActivityTypeEnum.cricket}


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def _category(score: float) -> str:
    if score < 30:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 70:
        return "High"
    return "Critical"


def _avg(values: List[float]):
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


def _sorted_reports(reports_with_videos: List[Tuple[models.Video, models.BiomechanicsReport]]):
    return sorted(reports_with_videos, key=lambda vr: vr[0].uploaded_at)


# ---------- Component scores ----------

def _biomechanical_deviation_score(reports):
    """Higher when videos show lower movement quality (i.e. bigger
    deviations from good technique)."""
    quality_scores = [r.movement_quality_score for _, r in reports if r.movement_quality_score is not None]
    if not quality_scores:
        return 50.0  # no data yet — neutral default, not asserting risk either way
    avg_quality = sum(quality_scores) / len(quality_scores)
    return round(_clamp(100 - avg_quality), 1)


def _movement_asymmetry_score(reports):
    symmetry_scores = [r.movement_symmetry_score for _, r in reports if r.movement_symmetry_score is not None]
    if not symmetry_scores:
        return 50.0
    avg_symmetry = sum(symmetry_scores) / len(symmetry_scores)
    return round(_clamp(100 - avg_symmetry), 1)


def _fatigue_score(reports):
    ordered = _sorted_reports(reports)
    scores = [r.movement_quality_score for _, r in ordered if r.movement_quality_score is not None]
    if len(scores) < 2:
        return 25.0
    *previous, latest = scores
    prev_avg = sum(previous) / len(previous)
    drop = prev_avg - latest
    # Every 5-point drop in quality score vs. baseline adds ~10 fatigue points.
    return round(_clamp(50 + drop * 2), 1)


# ---------- Injury-category scores ----------

def _injury_categories(reports, athlete):
    avg_valgus = _avg([r.knee_valgus_score for _, r in reports])
    avg_landing = _avg([r.landing_mechanics_score for _, r in reports])
    avg_symmetry = _avg([r.movement_symmetry_score for _, r in reports])
    avg_balance = _avg([r.balance_score for _, r in reports])
    avg_alignment = _avg([r.joint_alignment_score for _, r in reports])
    avg_hip_stability = _avg([r.hip_stability_score for _, r in reports])
    avg_trunk_lean = _avg([r.trunk_lean_degrees for _, r in reports])
    training_score = TRAINING_LOAD_SCORE[athlete.training_load_level]
    fatigue = _fatigue_score(reports)

    trunk_lean_proxy = _clamp(avg_trunk_lean * 3) if avg_trunk_lean is not None else None
    has_throwing_videos = any(v.activity_type in THROWING_ACTIVITIES for v, _ in reports)

    categories = []

    if avg_valgus is not None or avg_landing is not None:
        score = round(_clamp(
            0.6 * (avg_valgus or 30) + 0.4 * (100 - (avg_landing if avg_landing is not None else 60))
        ), 1)
        categories.append({
            "name": "ACL Injury Risk",
            "score": score,
            "note": "Driven by knee valgus and landing mechanics — the two most-cited "
                    "biomechanical ACL risk factors in the sports-medicine literature.",
        })
    else:
        categories.append({"name": "ACL Injury Risk", "score": 30.0,
                            "note": "Not enough landing/jumping video data yet."})

    if avg_symmetry is not None:
        score = round(_clamp(0.7 * (100 - avg_symmetry) + 0.3 * training_score), 1)
        categories.append({
            "name": "Hamstring Injury Risk", "score": score,
            "note": "Driven by left/right movement asymmetry and training load.",
        })
    else:
        categories.append({"name": "Hamstring Injury Risk", "score": 30.0, "note": "No symmetry data yet."})

    if avg_balance is not None or avg_alignment is not None:
        score = round(_clamp(
            0.6 * (100 - (avg_balance if avg_balance is not None else 60))
            + 0.4 * (100 - (avg_alignment if avg_alignment is not None else 60))
        ), 1)
        categories.append({
            "name": "Ankle Sprain Risk", "score": score,
            "note": "Driven by balance stability and joint alignment during movement.",
        })
    else:
        categories.append({"name": "Ankle Sprain Risk", "score": 30.0, "note": "No balance data yet."})

    if has_throwing_videos and trunk_lean_proxy is not None:
        score = round(_clamp(trunk_lean_proxy), 1)
        categories.append({
            "name": "Shoulder Injury Risk", "score": score,
            "note": "Based on trunk lean during throwing/bowling activity clips.",
        })
    else:
        categories.append({"name": "Shoulder Injury Risk", "score": 20.0,
                            "note": "No throwing/bowling-specific video data yet."})

    if trunk_lean_proxy is not None or avg_hip_stability is not None:
        score = round(_clamp(
            0.5 * (trunk_lean_proxy if trunk_lean_proxy is not None else 30)
            + 0.5 * (100 - (avg_hip_stability if avg_hip_stability is not None else 60))
        ), 1)
        categories.append({
            "name": "Lower Back Injury Risk", "score": score,
            "note": "Driven by trunk control and hip stability during movement.",
        })
    else:
        categories.append({"name": "Lower Back Injury Risk", "score": 30.0, "note": "Not enough data yet."})

    score = round(_clamp(0.6 * training_score + 0.4 * fatigue), 1)
    categories.append({
        "name": "Overuse Injury Risk", "score": score,
        "note": "Driven by training load level and recent fatigue/performance-decline signal.",
    })

    return [
        {"name": c["name"], "score": c["score"], "category": _category(c["score"]), "note": c["note"]}
        for c in categories
    ]


# ---------- Movement anomaly detection ----------

def _detect_anomalies(reports):
    anomalies = []
    if len(reports) < 2:
        return anomalies

    ordered = _sorted_reports(reports)

    for video, report in ordered:
        others_quality = [r.movement_quality_score for v, r in ordered
                           if r.movement_quality_score is not None and v.id != video.id]
        if report.movement_quality_score is not None and others_quality:
            baseline = sum(others_quality) / len(others_quality)
            if baseline - report.movement_quality_score >= 15:
                anomalies.append({
                    "video_id": video.id, "filename": video.filename,
                    "description": (
                        f"Movement quality ({report.movement_quality_score}) dropped "
                        f"notably below this athlete's baseline ({round(baseline, 1)}) — "
                        f"possible technique breakdown or fatigue."
                    ),
                })

        others_valgus = [r_.knee_valgus_score for v_, r_ in ordered
                          if r_.knee_valgus_score is not None and v_.id != video.id]
        if report.knee_valgus_score is not None and others_valgus:
            baseline_v = sum(others_valgus) / len(others_valgus)
            if report.knee_valgus_score - baseline_v >= 20:
                anomalies.append({
                    "video_id": video.id, "filename": video.filename,
                    "description": (
                        f"Knee valgus score ({report.knee_valgus_score}) spiked well above "
                        f"this athlete's baseline ({round(baseline_v, 1)}) in this clip."
                    ),
                })

    return anomalies


# ---------- Corrective recommendations ----------

def _recommendations(components: dict, injury_categories: List[dict], athlete) -> List[dict]:
    recs = []

    def has_high_risk(name):
        return any(c["name"] == name and c["score"] >= 50 for c in injury_categories)

    if has_high_risk("ACL Injury Risk"):
        recs.append({"category": "Strengthening",
                      "text": "Add hip abductor and glute strengthening (banded lateral walks, "
                              "clamshells) to reduce inward knee collapse during landing and cutting."})
        recs.append({"category": "Exercise",
                      "text": "Incorporate soft-landing plyometric drills that emphasize knee-over-toe "
                              "alignment on touchdown."})

    if has_high_risk("Hamstring Injury Risk"):
        recs.append({"category": "Strengthening",
                      "text": "Add eccentric hamstring work (Nordic curls, Romanian deadlifts) and "
                              "address the left/right strength imbalance driving asymmetry."})

    if has_high_risk("Ankle Sprain Risk"):
        recs.append({"category": "Mobility",
                      "text": "Add single-leg balance and proprioception drills (wobble board, "
                              "single-leg RDL) to improve ankle stability."})

    if has_high_risk("Shoulder Injury Risk"):
        recs.append({"category": "Mobility",
                      "text": "Add rotator cuff and scapular stability work; review throwing/bowling "
                              "mechanics with a coach."})

    if has_high_risk("Lower Back Injury Risk"):
        recs.append({"category": "Strengthening",
                      "text": "Add core and anti-rotation strengthening (dead bugs, Pallof press) "
                              "and review trunk control during movement."})

    if has_high_risk("Overuse Injury Risk") or components["training_load"]["score"] >= 70:
        recs.append({"category": "Training Modification",
                      "text": "Reduce weekly training volume or add an extra recovery day; "
                              "monitor training load closely over the next 2-3 weeks."})

    if components["fatigue_indicators"]["score"] >= 50:
        recs.append({"category": "Recovery",
                      "text": "Prioritize sleep and recovery protocols. Consider a deload week if "
                              "movement quality keeps trending down across sessions."})

    if components["historical_injury_factors"]["score"] >= 65:
        recs.append({"category": "Recovery",
                      "text": "Given this athlete's injury history, coordinate with a physiotherapist "
                              "before increasing training intensity or volume."})

    if not recs:
        recs.append({"category": "General",
                      "text": "No significant risk factors detected in the current data — maintain "
                              "the current training and monitoring routine."})

    return recs


# ---------- Public entry point ----------

def build_risk_assessment(athlete, reports_with_videos: List[Tuple[models.Video, models.BiomechanicsReport]]) -> dict:
    if not reports_with_videos:
        return {
            "athlete_id": athlete.id,
            "video_count": 0,
            "overall_score": None,
            "overall_category": None,
            "components": [],
            "injury_categories": [],
            "anomalies": [],
            "recommendations": [],
            "message": "No completed video reports yet — upload and process at least one video "
                       "to generate an injury risk assessment.",
            "generated_at": datetime.utcnow(),
        }

    biomech = _biomechanical_deviation_score(reports_with_videos)
    hist = INJURY_SEVERITY_SCORE[athlete.injury_severity]
    asymmetry = _movement_asymmetry_score(reports_with_videos)
    training = TRAINING_LOAD_SCORE[athlete.training_load_level]
    fatigue = _fatigue_score(reports_with_videos)

    component_map = {
        "biomechanical_deviations": {"label": "Biomechanical Deviations", "weight_pct": 35, "score": biomech},
        "historical_injury_factors": {"label": "Historical Injury Factors", "weight_pct": 20, "score": hist},
        "movement_asymmetry": {"label": "Movement Asymmetry", "weight_pct": 20, "score": asymmetry},
        "training_load": {"label": "Training Load Indicators", "weight_pct": 15, "score": training},
        "fatigue_indicators": {"label": "Fatigue Indicators", "weight_pct": 10, "score": fatigue},
    }

    overall = sum(WEIGHTS[k] * component_map[k]["score"] for k in WEIGHTS)
    overall = round(_clamp(overall), 1)

    injury_categories = _injury_categories(reports_with_videos, athlete)
    anomalies = _detect_anomalies(reports_with_videos)
    recommendations = _recommendations(component_map, injury_categories, athlete)

    components = [
        {"label": v["label"], "weight_pct": v["weight_pct"], "score": v["score"], "category": _category(v["score"])}
        for v in component_map.values()
    ]

    return {
        "athlete_id": athlete.id,
        "video_count": len(reports_with_videos),
        "overall_score": overall,
        "overall_category": _category(overall),
        "components": components,
        "injury_categories": injury_categories,
        "anomalies": anomalies,
        "recommendations": recommendations,
        "message": None,
        "generated_at": datetime.utcnow(),
    }
