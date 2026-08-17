import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

const emptyForm = {
  athlete_code: "", sport_type: "", position: "", age: "",
  height_cm: "", weight_kg: "", injury_history: "", training_load: "",
  injury_severity: "none", training_load_level: "moderate",
};

const INJURY_SEVERITY_OPTIONS = ["none", "mild", "moderate", "severe"];
const TRAINING_LOAD_LEVEL_OPTIONS = ["low", "moderate", "high", "very_high"];

export default function AthleteForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (isEdit) {
      api.getAthlete(id).then((data) => setForm({ ...data })).catch((err) => setError(err.message));
    }
  }, [id]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const payload = {
      ...form,
      age: Number(form.age),
      height_cm: Number(form.height_cm),
      weight_kg: Number(form.weight_kg),
    };
    try {
      if (isEdit) {
        const { athlete_code, ...updatable } = payload;
        await api.updateAthlete(id, updatable);
      } else {
        await api.createAthlete(payload);
      }
      navigate("/athletes");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h2>{isEdit ? "Edit Athlete" : "New Athlete"}</h2>
      <form className="card" onSubmit={handleSubmit}>
        {error && <p className="error">{error}</p>}

        <label>Athlete Code</label>
        <input name="athlete_code" value={form.athlete_code} onChange={handleChange} disabled={isEdit} required />

        <label>Sport Type</label>
        <input name="sport_type" value={form.sport_type} onChange={handleChange} required />

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
        <p className="muted" style={{ marginTop: 4 }}>Used by the Injury Risk Prediction Engine — pick the best match for this athlete's history.</p>

        <label>Training Load (notes)</label>
        <input name="training_load" value={form.training_load || ""} onChange={handleChange} placeholder="e.g. High — 6 sessions/week" />

        <label>Training Load Level</label>
        <select name="training_load_level" value={form.training_load_level} onChange={handleChange}>
          {TRAINING_LOAD_LEVEL_OPTIONS.map((o) => <option key={o} value={o}>{o.replace("_", " ")}</option>)}
        </select>

        <button type="submit" disabled={loading}>{loading ? "Saving..." : "Save"}</button>
      </form>
    </div>
  );
}
