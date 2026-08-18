import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { api } from "../api";
import PoseLoader from "../components/PoseLoader";
import { EmptyIllustration } from "../components/Illustrations";

const RISK_COLORS = {
  Low: "#1E9E5A",
  Moderate: "#D69A00",
  High: "#E8672A",
  Critical: "#D93A3A",
};

export default function TeamOverview() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTeamOverview()
      .then(setEntries)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><PoseLoader text="Loading team overview..." /></div>;
  if (error) return <div className="page"><p className="error">{error}</p></div>;

  const needingAttention = entries.filter((e) => e.needs_attention);

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>Team Overview</h2>
      </div>

      {needingAttention.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <AlertTriangle size={18} color="#E8672A" /> Needs Attention ({needingAttention.length})
          </h3>
          {needingAttention.map((e) => (
            <div className="anomaly-card" key={e.athlete_id}>
              <AlertTriangle size={18} strokeWidth={2} />
              <div>
                <p className="anomaly-video">{e.athlete_code} — {e.sport_type}</p>
                <p className="muted">
                  Injury severity: {e.injury_severity}
                  {e.latest_risk_category && ` · Latest risk: ${e.latest_risk_category}`}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {entries.length === 0 ? (
        <div className="card empty-state">
          <EmptyIllustration className="empty-illustration" />
          <p>No athlete profiles yet.</p>
        </div>
      ) : (
        <div className="card">
          <h3>All Athletes</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Athlete</th><th>Sport</th><th>Injury Severity</th>
                <th>Training Load</th><th>Videos</th><th>Latest Score</th>
                <th>Latest Risk</th><th></th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.athlete_id}>
                  <td>{e.athlete_code}</td>
                  <td>{e.sport_type}</td>
                  <td>{e.injury_severity}</td>
                  <td>{e.training_load_level.replace("_", " ")}</td>
                  <td>{e.video_count}</td>
                  <td>{e.latest_movement_quality_score ?? "-"}</td>
                  <td>
                    {e.latest_risk_category ? (
                      <span className="badge badge-risk" style={{ background: RISK_COLORS[e.latest_risk_category] }}>
                        {e.latest_risk_category}
                      </span>
                    ) : "-"}
                  </td>
                  <td className="table-actions">
                    <Link to={`/athletes/${e.athlete_id}`}>View</Link>
                    {" | "}
                    <Link to={`/athletes/${e.athlete_id}/risk-assessment`}>Risk Assessment</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
