import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import {
  Dumbbell, Activity, Move, Moon, SlidersHorizontal, Info, AlertTriangle,
} from "lucide-react";
import { api, triggerDownload } from "../api";
import ScoreGauge from "../components/ScoreGauge";
import PoseLoader from "../components/PoseLoader";

const RISK_COLORS = {
  Low: "#1E9E5A",
  Moderate: "#D69A00",
  High: "#E8672A",
  Critical: "#D93A3A",
  Unknown: "#8B94A3",
};

const CATEGORY_ICONS = {
  Exercise: Activity,
  Mobility: Move,
  Strengthening: Dumbbell,
  Recovery: Moon,
  "Training Modification": SlidersHorizontal,
  General: Info,
};

function riskColor(score) {
  if (score >= 70) return RISK_COLORS.Critical;
  if (score >= 50) return RISK_COLORS.High;
  if (score >= 30) return RISK_COLORS.Moderate;
  return RISK_COLORS.Low;
}

export default function RiskAssessment() {
  const { id } = useParams();
  const [assessment, setAssessment] = useState(null);
  const [athlete, setAthlete] = useState(null);
  const [error, setError] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [a, r] = await Promise.all([api.getAthlete(id), api.getRiskAssessment(id)]);
        setAthlete(a);
        setAssessment(r);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleDownload = async () => {
    setDownloadError("");
    setDownloading(true);
    try {
      const blob = await api.downloadRiskAssessmentPdf(id);
      triggerDownload(blob, `${athlete.athlete_code}_risk_assessment.pdf`);
    } catch (err) {
      setDownloadError(err.message);
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <div className="page"><PoseLoader text="Running injury risk prediction..." /></div>;
  if (error) return <div className="page"><p className="error">{error}</p></div>;
  if (!assessment) return null;

  const componentChartData = assessment.components.map((c) => ({
    name: `${c.label} (${c.weight_pct}%)`,
    value: c.score,
  }));
  const categoryChartData = assessment.injury_categories.map((c) => ({
    name: c.name.replace(" Injury Risk", "").replace(" Sprain Risk", ""),
    value: c.score,
  }));

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>Injury Risk Assessment {athlete ? `— ${athlete.athlete_code}` : ""}</h2>
        <Link to={`/athletes/${id}`}>&larr; Back to profile</Link>
      </div>

      {assessment.video_count === 0 ? (
        <div className="card">
          <p className="muted">{assessment.message}</p>
        </div>
      ) : (
        <>
          <div className="card report-hero">
            <ScoreGauge
              score={assessment.overall_score}
              label="Injury Risk Score"
              riskCategory={assessment.overall_category}
              size={180}
            />
            <div className="report-hero-details">
              <span className="badge badge-risk" style={{ background: RISK_COLORS[assessment.overall_category] }}>
                {assessment.overall_category} Risk
              </span>
              <p className="muted">
                Weighted score from {assessment.video_count} processed video(s): biomechanical
                deviations, historical injury factors, movement asymmetry, training load, and
                fatigue indicators. Higher score = higher predicted risk.
              </p>
              <button onClick={handleDownload} disabled={downloading}>
                {downloading ? "Generating..." : "Download PDF Report"}
              </button>
              {downloadError && (
                <p className="error" style={{ marginTop: 10 }}>
                  {downloadError === "Failed to fetch"
                    ? "Could not reach the backend server. Confirm it's running at http://127.0.0.1:8000 and try again."
                    : downloadError}
                </p>
              )}
            </div>
          </div>

          <div className="card">
            <h3>Weighted Risk Components</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={componentChartData} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D6DDD3" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={70} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {componentChartData.map((entry, idx) => (
                    <Cell key={idx} fill={riskColor(entry.value)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3>Injury Category Breakdown</h3>
            <p className="muted" style={{ marginTop: -6 }}>
              Elevated-risk indicators derived from biomechanical metrics most associated with
              each injury type — not clinical probabilities.
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categoryChartData} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D6DDD3" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={70} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {categoryChartData.map((entry, idx) => (
                    <Cell key={idx} fill={riskColor(entry.value)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <table className="table" style={{ marginTop: 14 }}>
              <thead><tr><th>Category</th><th>Note</th></tr></thead>
              <tbody>
                {assessment.injury_categories.map((c) => (
                  <tr key={c.name}>
                    <td>{c.name}</td>
                    <td style={{ fontFamily: "var(--font-body)" }} className="muted">{c.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {assessment.anomalies.length > 0 && (
            <div className="card">
              <h3>Movement Anomalies Detected</h3>
              {assessment.anomalies.map((a, i) => (
                <div key={i} className="anomaly-card">
                  <AlertTriangle size={18} strokeWidth={2} />
                  <div>
                    <p className="anomaly-video">{a.filename}</p>
                    <p className="muted">{a.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="card">
            <h3>Corrective Recommendations</h3>
            <div className="recommendation-grid">
              {assessment.recommendations.map((r, i) => {
                const Icon = CATEGORY_ICONS[r.category] || Info;
                return (
                  <div className="recommendation-card" key={i}>
                    <div className="recommendation-icon"><Icon size={18} strokeWidth={2} /></div>
                    <div>
                      <p className="recommendation-category">{r.category}</p>
                      <p className="recommendation-text">{r.text}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <p className="muted" style={{ fontSize: "0.8rem" }}>
            This is a non-clinical, heuristic risk assessment derived from simplified 2D
            pose-estimation metrics, self-reported injury history, and training load. It is not
            a medical diagnosis and does not replace evaluation by a qualified physiotherapist
            or sports medicine physician.
          </p>
        </>
      )}
    </div>
  );
}
