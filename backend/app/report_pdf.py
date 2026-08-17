from datetime import datetime

from fpdf import FPDF


def _safe(text) -> str:
    """Coerce to str and strip/replace any character fpdf2's core fonts
    can't render, instead of letting it crash PDF generation."""
    if text is None:
        return "-"
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _cell(pdf: FPDF, w, h, text="", **kwargs):
    pdf.cell(w, h, _safe(text), **kwargs)


def _multicell(pdf: FPDF, w, h, text="", **kwargs):
    pdf.multi_cell(w, h, _safe(text), **kwargs)


def _header(pdf: FPDF, title: str, subtitle: str = None):
    pdf.set_font("Helvetica", "B", 18)
    _cell(pdf, 0, 12, title, ln=True)
    if subtitle:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(90, 90, 90)
        _cell(pdf, 0, 8, subtitle, ln=True)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(4)


def _section(pdf: FPDF, title: str):
    pdf.set_font("Helvetica", "B", 13)
    _cell(pdf, 0, 9, title, ln=True)
    pdf.ln(1)


def _row(pdf: FPDF, label: str, value):
    pdf.set_font("Helvetica", "B", 11)
    _cell(pdf, 75, 8, label)
    pdf.set_font("Helvetica", "", 11)
    _cell(pdf, 0, 8, "-" if value is None else value, ln=True)


def _fmt(value, suffix=""):
    return "-" if value is None else f"{value}{suffix}"


def _risk_rgb(category: str):
    """Same risk-category color scale used on the website."""
    return {
        "Low": (30, 158, 90),
        "Moderate": (214, 154, 0),
        "High": (232, 103, 42),
        "Critical": (217, 58, 58),
    }.get(category, (139, 148, 163))


def _bar_row(pdf: FPDF, label: str, score, category: str, page_width: float, bar_h: float = 7.5):
    """Draws one horizontal bar-chart row: label | filled bar (0-100) | value.
    Mirrors the bar charts shown on the Risk Assessment web page."""
    label_w = page_width * 0.44
    bar_w = page_width * 0.36
    score_w = page_width - label_w - bar_w - 2

    start_x = pdf.get_x()
    y = pdf.get_y()

    pdf.set_font("Helvetica", "", 9)
    _cell(pdf, label_w, bar_h, label)

    bar_x = pdf.get_x()
    inner_h = bar_h - 2.6
    pdf.set_fill_color(228, 233, 225)
    pdf.rect(bar_x, y + 1.3, bar_w, inner_h, style="F")
    if score is not None:
        r, g, b = _risk_rgb(category)
        pdf.set_fill_color(r, g, b)
        filled = bar_w * max(0.0, min(100.0, score)) / 100.0
        if filled > 0:
            pdf.rect(bar_x, y + 1.3, filled, inner_h, style="F")

    pdf.set_xy(bar_x + bar_w + 2, y)
    pdf.set_font("Helvetica", "B", 9)
    _cell(pdf, score_w, bar_h, _fmt(score), ln=True)
    pdf.set_x(start_x)


def build_video_report_pdf(video, report, athlete) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    _header(
        pdf, "Biomechanics Report",
        f"Athlete: {athlete.athlete_code}  |  Sport: {athlete.sport_type}  |  Video: {video.filename}",
    )
    pdf.set_font("Helvetica", "", 10)
    _cell(pdf, 0, 6, f"Activity type: {video.activity_type.value.replace('_', ' ')}", ln=True)
    _cell(pdf, 0, 6, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 16)
    _cell(pdf, 0, 10, f"Movement Quality Score: {_fmt(report.movement_quality_score, ' / 100')}", ln=True)
    pdf.set_font("Helvetica", "B", 13)
    _cell(pdf, 0, 8, f"Risk Category: {report.risk_category or 'Unknown'}", ln=True)
    pdf.ln(5)

    _section(pdf, "Biomechanical Metrics (0-100 scale)")
    _row(pdf, "Hip Stability", report.hip_stability_score)
    _row(pdf, "Landing Mechanics", report.landing_mechanics_score)
    _row(pdf, "Joint Alignment", report.joint_alignment_score)
    _row(pdf, "Balance", report.balance_score)
    _row(pdf, "Movement Symmetry", report.movement_symmetry_score)
    _row(pdf, "Knee Valgus Score", report.knee_valgus_score)
    pdf.ln(4)

    _section(pdf, "Raw Joint Measurements")
    _row(pdf, "Avg. Left Knee Angle", _fmt(report.avg_left_knee_angle, " deg"))
    _row(pdf, "Avg. Right Knee Angle", _fmt(report.avg_right_knee_angle, " deg"))
    _row(pdf, "Trunk Lean", _fmt(report.trunk_lean_degrees, " deg"))
    _row(pdf, "Stride Length Ratio", report.stride_length_ratio)
    pdf.ln(4)

    if video.duration_seconds or video.frames_processed:
        _section(pdf, "Processing Info")
        _row(pdf, "Video Duration", _fmt(video.duration_seconds, "s"))
        _row(pdf, "Frames Analyzed", video.frames_processed)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    _multicell(
        pdf, 0, 5,
        "Note: metrics are derived from single-camera 2D pose estimation and are "
        "simplified heuristics, not clinically validated biomechanical measurements.",
    )

    return bytes(pdf.output())


def build_summary_report_pdf(athlete, reports_with_videos) -> bytes:
    """reports_with_videos: list of (video, report) tuples, completed videos only."""
    pdf = FPDF()
    pdf.add_page()

    _header(
        pdf, "Combined Biomechanics Report",
        f"Athlete: {athlete.athlete_code}  |  Sport: {athlete.sport_type}  |  "
        f"{len(reports_with_videos)} video(s) analyzed",
    )
    pdf.set_font("Helvetica", "", 10)
    _cell(pdf, 0, 6, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.ln(6)

    def avg_field(field):
        vals = [getattr(r, field) for _, r in reports_with_videos if getattr(r, field) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    overall = avg_field("movement_quality_score")
    pdf.set_font("Helvetica", "B", 16)
    _cell(pdf, 0, 10, f"Average Movement Quality Score: {_fmt(overall, ' / 100')}", ln=True)
    pdf.ln(4)

    _section(pdf, "Average Metrics Across All Videos")
    _row(pdf, "Hip Stability", avg_field("hip_stability_score"))
    _row(pdf, "Landing Mechanics", avg_field("landing_mechanics_score"))
    _row(pdf, "Joint Alignment", avg_field("joint_alignment_score"))
    _row(pdf, "Balance", avg_field("balance_score"))
    _row(pdf, "Movement Symmetry", avg_field("movement_symmetry_score"))
    _row(pdf, "Knee Valgus Score", avg_field("knee_valgus_score"))
    pdf.ln(6)

    _section(pdf, "Per-Video Breakdown")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 233, 225)
    _cell(pdf, 55, 8, "Video", border=1, fill=True)
    _cell(pdf, 35, 8, "Activity", border=1, fill=True)
    _cell(pdf, 35, 8, "Quality Score", border=1, fill=True)
    _cell(pdf, 30, 8, "Risk", border=1, fill=True)
    _cell(pdf, 30, 8, "Uploaded", border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for video, report in sorted(reports_with_videos, key=lambda vr: vr[0].uploaded_at):
        name = video.filename if len(video.filename) <= 26 else video.filename[:23] + "..."
        _cell(pdf, 55, 8, name, border=1)
        _cell(pdf, 35, 8, video.activity_type.value.replace("_", " "), border=1)
        _cell(pdf, 35, 8, _fmt(report.movement_quality_score), border=1)
        _cell(pdf, 30, 8, report.risk_category or "-", border=1)
        _cell(pdf, 30, 8, video.uploaded_at.strftime("%Y-%m-%d"), border=1)
        pdf.ln()

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    _multicell(
        pdf, 0, 5,
        "Note: this combined report averages simplified 2D pose-estimation heuristics "
        "across all completed videos for this athlete. It is not a clinically validated "
        "biomechanical assessment.",
    )

    return bytes(pdf.output())


def build_risk_assessment_pdf(athlete, assessment: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    _header(
        pdf, "Injury Risk Assessment",
        f"Athlete: {athlete.athlete_code}  |  Sport: {athlete.sport_type}  |  "
        f"Based on {assessment['video_count']} video(s)",
    )
    pdf.set_font("Helvetica", "", 10)
    _cell(pdf, 0, 6, f"Generated: {assessment['generated_at'].strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 16)
    _cell(pdf, 0, 10, f"Overall Injury Risk Score: {_fmt(assessment['overall_score'], ' / 100')}", ln=True)
    pdf.set_font("Helvetica", "B", 13)
    _cell(pdf, 0, 8, f"Risk Category: {assessment['overall_category'] or 'Unknown'}", ln=True)
    pdf.ln(5)

    # ---------- Weighted Risk Components (bar chart) ----------
    _section(pdf, "Weighted Risk Components")
    for c in assessment["components"]:
        _bar_row(pdf, f"{c['label']} ({c['weight_pct']}%)", c["score"], c["category"], page_width)
    pdf.ln(4)

    # ---------- Injury Category Breakdown (bar chart) ----------
    _section(pdf, "Injury Category Breakdown")
    for cat in assessment["injury_categories"]:
        _bar_row(pdf, cat["name"], cat["score"], cat["category"], page_width)
    pdf.ln(4)

    # ---------- Category + Note detail (mirrors the table under the chart on the site) ----------
    pdf.set_font("Helvetica", "B", 10)
    _cell(pdf, 0, 6, "Category Notes", ln=True)
    pdf.ln(1)
    for cat in assessment["injury_categories"]:
        r, g, b = _risk_rgb(cat["category"])
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(r, g, b)
        _cell(pdf, 0, 5, f"{cat['name']}: {_fmt(cat['score'])} / 100  ({cat['category']})", ln=True)
        pdf.set_text_color(80, 80, 80)
        pdf.set_font("Helvetica", "", 9)
        _multicell(pdf, 0, 5, cat.get("note") or "-")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1.5)
    pdf.ln(2)

    # ---------- Movement Anomalies ----------
    if assessment["anomalies"]:
        _section(pdf, "Movement Anomalies Detected")
        pdf.set_font("Helvetica", "", 10)
        for a in assessment["anomalies"]:
            _multicell(pdf, 0, 6, f"- [{a['filename']}] {a['description']}")
        pdf.ln(3)

    # ---------- Corrective Recommendations ----------
    _section(pdf, "Corrective Recommendations")
    for r in assessment["recommendations"]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(58, 54, 224)
        _cell(pdf, 0, 6, r["category"].upper(), ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        _multicell(pdf, 0, 6, r["text"])
        pdf.ln(1.5)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    _multicell(
        pdf, 0, 5,
        "Note: this is a non-clinical, heuristic risk assessment derived from simplified "
        "2D pose-estimation metrics, self-reported injury history, and training load. It "
        "is not a medical diagnosis and does not replace evaluation by a qualified "
        "physiotherapist or sports medicine physician.",
    )

    return bytes(pdf.output())
