import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, triggerDownload } from "../api";
import PoseLoader from "../components/PoseLoader";

const emptyForm = {
  athlete_code: "", sport_type: "", position: "", age: "",
  height_cm: "", weight_kg: "", injury_history: "", training_load: "",
  injury_severity: "none", training_load_level: "moderate",
};

const INJURY_SEVERITY_OPTIONS = ["none", "mild", "moderate", "severe"];
const TRAINING_LOAD_LEVEL_OPTIONS = ["low", "moderate", "high", "very_high"];

export default function MyProfile() {
  const [athlete, setAthlete] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [summary, setSummary] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadingExcel, setDownloadingExcel] = useState(false);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.getMyAthlete();
      setAthlete(data);
      setForm({ ...data });
      setNotFound(false);
      try {
        const s = await api.getAthleteReportsSummary(data.id);
        setSummary(s);
      } catch (_) {
        setSummary(null);
      }
    } catch (err) {
      if (err.message.toLowerCase().includes("haven't created")) {
        setNotFound(true);
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const numeric = (f) => ({
    ...f,
    age: Number(f.age),
    height_cm: Number(f.height_cm),
    weight_kg: Number(f.weight_kg),
  });

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const created = await api.createMyAthlete(numeric(form));
      setAthlete(created);
      setForm({ ...created });
      setNotFound(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const { athlete_code, ...updatable } = numeric(form);
      const updated = await api.updateMyAthlete(updatable);
      setAthlete(updated);
      setEditing(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadSummary = async () => {
    setError("");
    setDownloading(true);
    try {
      const blob = await api.downloadAthleteSummaryPdf(athlete.id);
      triggerDownload(blob, `${athlete.athlete_code}_combined_report.pdf`);
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloading(false);
    }
  };

  const handleDownloadExcel = async () => {
    setError("");
    setDownloadingExcel(true);
    try {
      const blob = await api.downloadAthleteSummaryExcel(athlete.id);
      triggerDownload(blob, `${athlete.athlete_code}_combined_report.xlsx`);
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloadingExcel(false);
    }
  };

  if (loading) return <div className="page"><PoseLoader text="Loading your profile..." /></div>;

  // ---------- No profile yet: show creation form ----------
  if (notFound) {
    return (
      <div className="page fade-in">
        <div className="page-header"><h2>Create Your Athlete Profile</h2></div>
        <div className="card">
          <p className="muted">
            You haven't set up your athlete profile yet. Fill this in once — your
            coach and physio will use it to track your movement analysis, and
            you'll be able to upload your own videos right after.
          </p>
          <form onSubmit={handleCreate}>
            {error && <p className="error">{error}</p>}
            <label>Athlete Code</label>
            <input name="athlete_code" value={form.athlete_code} onChange={handleChange} required />
            <label>Sport Type</label>
            <input name="sport_type" value={form.sport_type} onChange={handleChange} required />
            <label>Position</label>
            <input name="position" value={form.position} onChange={handleChange} />
            <label>Age</label>
            <input type="number" name="age" value={form.age} onChange={handleChange} required />
            <label>Height (cm)</label>
            <input type="number" step="0.1" name="height_cm" value={form.height_cm} onChange={handleChange} required />
            <label>Weight (kg)</label>
            <input type="number" step="0.1" name="weight_kg" value={form.weight_kg} onChange={handleChange} required />
            <label>Injury History (notes)</label>
            <textarea name="injury_history" value={form.injury_history} onChange={handleChange} rows={3} />
            <label>Injury Severity</label>
            <select name="injury_severity" value={form.injury_severity} onChange={handleChange}>
              {INJURY_SEVERITY_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
            <p className="muted" style={{ marginTop: 4 }}>Used by the Injury Risk Prediction Engine — pick the option that best matches your history.</p>
            <label>Training Load (notes)</label>
            <input name="training_load" value={form.training_load} onChange={handleChange} placeholder="e.g. High — 6 sessions/week" />
            <label>Training Load Level</label>
            <select name="training_load_level" value={form.training_load_level} onChange={handleChange}>
              {TRAINING_LOAD_LEVEL_OPTIONS.map((o) => <option key={o} value={o}>{o.replace("_", " ")}</option>)}
            </select>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Create My Profile"}</button>
          </form>
        </div>
      </div>
    );
  }

  // ---------- Profile exists: view / edit + videos + combined report ----------
  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>My Profile</h2>
        <div style={{ display: "flex", gap: 12 }}>
          <Link className="btn" to={`/athletes/${athlete.id}/risk-assessment`}>View Injury Risk Assessment</Link>
          <Link className="btn btn-secondary" to={`/videos/upload?athlete_id=${athlete.id}`}>Upload Movement Video</Link>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {!editing ? (
        <div className="card">
          <p><strong>Athlete Code:</strong> {athlete.athlete_code}</p>
          <p><strong>Sport Type:</strong> {athlete.sport_type}</p>
          <p><strong>Position:</strong> {athlete.position || "-"}</p>
          <p><strong>Age:</strong> {athlete.age}</p>
          <p><strong>Height:</strong> {athlete.height_cm} cm</p>
          <p><strong>Weight:</strong> {athlete.weight_kg} kg</p>
          <p><strong>Training Load:</strong> {athlete.training_load || "-"} ({athlete.training_load_level?.replace("_", " ")})</p>
          <p><strong>Injury History:</strong> {athlete.injury_history || "None recorded"} ({athlete.injury_severity})</p>
          <button onClick={() => setEditing(true)}>Edit Profile</button>
        </div>
      ) : (
        <form className="card" onSubmit={handleUpdate}>
          <label>Sport Type</label>
          <input name="sport_type" value={form.sport_type || ""} onChange={handleChange} required />
          <label>Position</label>
          <input name="position" value={form.position || ""} onChange={handleChange} />
          <label>Age</label>
          <input type="number" name="age" value={form.age} onChange={handleChange} required />
          <label>Height (cm)</label>
          <input type="number" step="0.1" name="height_cm" value={form.height_cm} onChange={handleChange} required />
          <label>Weight (kg)</label>
          <input type="number" step="0.1" name="weight_kg" value={form.weight_kg} onChange={handleChange} required />
          <label>Injury History (notes)</label>
          <textarea name="injury_history" value={form.injury_history || ""} onChange={handleChange} rows={3} />
          <label>Injury Severity</label>
          <select name="injury_severity" value={form.injury_severity} onChange={handleChange}>
            {INJURY_SEVERITY_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
          <label>Training Load (notes)</label>
          <input name="training_load" value={form.training_load || ""} onChange={handleChange} />
          <label>Training Load Level</label>
          <select name="training_load_level" value={form.training_load_level} onChange={handleChange}>
            {TRAINING_LOAD_LEVEL_OPTIONS.map((o) => <option key={o} value={o}>{o.replace("_", " ")}</option>)}
          </select>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Save Changes"}</button>
            <button
              type="button" className="btn-secondary"
              onClick={() => { setEditing(false); setForm({ ...athlete }); }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="card" style={{ marginTop: 20 }}>
        <div className="page-header" style={{ marginBottom: summary?.video_count ? 16 : 0 }}>
          <h3 style={{ margin: 0 }}>
            Combined Report {summary?.video_count ? `— ${summary.video_count} video(s)` : ""}
          </h3>
          {summary?.video_count > 0 && (
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={handleDownloadSummary} disabled={downloading}>
                {downloading ? "Generating..." : "Download PDF"}
              </button>
              <button className="btn-secondary" onClick={handleDownloadExcel} disabled={downloadingExcel}>
                {downloadingExcel ? "Generating..." : "Download Excel"}
              </button>
            </div>
          )}
        </div>

        {!summary || summary.video_count === 0 ? (
          <p className="muted">
            {summary?.message || "Upload and process at least one video to see your combined report."}
          </p>
        ) : (
          <>
            <p><strong>Average Movement Quality Score:</strong> {summary.avg_movement_quality_score} / 100</p>
            <table className="table">
              <thead>
                <tr><th>Video</th><th>Activity</th><th>Score</th><th>Risk</th><th></th></tr>
              </thead>
              <tbody>
                {summary.videos.map((v) => (
                  <tr key={v.video_id}>
                    <td>{v.filename}</td>
                    <td>{v.activity_type.replace("_", " ")}</td>
                    <td>{v.movement_quality_score ?? "-"}</td>
                    <td>{v.risk_category || "-"}</td>
                    <td><Link to={`/videos/${v.video_id}`}>View</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}
