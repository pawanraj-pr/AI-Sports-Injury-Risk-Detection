const BASE_URL = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("access_token");
}

async function request(path, { method = "GET", body, auth = true, form = false } = {}) {
  const headers = {};
  if (!form) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: form ? body : body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = "Request failed";
    try {
      const errJson = await res.json();
      detail = errJson.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  register: (data) => request("/auth/register", { method: "POST", body: data, auth: false }),

  login: (email, password) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    return request("/auth/login", { method: "POST", body: form, auth: false, form: true });
  },

  me: () => request("/auth/me"),

  listAthletes: () => request("/athletes/"),
  getAthlete: (id) => request(`/athletes/${id}`),
  createAthlete: (data) => request("/athletes/", { method: "POST", body: data }),
  updateAthlete: (id, data) => request(`/athletes/${id}`, { method: "PUT", body: data }),
  deleteAthlete: (id) => request(`/athletes/${id}`, { method: "DELETE" }),

  // Self-service athlete profile (athlete-role accounts managing their own record)
  getMyAthlete: () => request("/athletes/me"),
  createMyAthlete: (data) => request("/athletes/me", { method: "POST", body: data }),
  updateMyAthlete: (data) => request("/athletes/me", { method: "PUT", body: data }),

  // Combined / summary reports across all of an athlete's videos
  getAthleteReportsSummary: (athleteId) => request(`/athletes/${athleteId}/reports/summary`),
  downloadAthleteSummaryPdf: (athleteId) => downloadBlob(`/athletes/${athleteId}/reports/summary/pdf`),
  downloadVideoReportPdf: (videoId) => downloadBlob(`/videos/${videoId}/report/pdf`),

  // Injury Risk Prediction / Anomaly Detection / Recommendations (Milestone 3)
  getRiskAssessment: (athleteId) => request(`/athletes/${athleteId}/risk-assessment`),
  downloadRiskAssessmentPdf: (athleteId) => downloadBlob(`/athletes/${athleteId}/risk-assessment/pdf`),

  // Videos / Pose Estimation / Biomechanics (Milestone 2)
  uploadVideo: async (athleteId, activityType, file) => {
    const form = new FormData();
    form.append("athlete_id", athleteId);
    form.append("activity_type", activityType);
    form.append("file", file);
    const token = getToken();
    const res = await fetch(`${BASE_URL}/videos/upload`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) {
      let detail = "Upload failed";
      try { detail = (await res.json()).detail || detail; } catch (_) {}
      throw new Error(detail);
    }
    return res.json();
  },
  processVideo: (id) => request(`/videos/${id}/process`, { method: "POST" }),
  listVideos: (athleteId) =>
    request(`/videos/${athleteId ? `?athlete_id=${athleteId}` : ""}`),
  getVideo: (id) => request(`/videos/${id}`),
  deleteVideo: (id) => request(`/videos/${id}`, { method: "DELETE" }),
};

// Fetches a PDF as a blob (auth'd) — separate from `request` since responses
// here are binary, not JSON.
async function downloadBlob(path) {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    let detail = "Could not generate PDF";
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return res.blob();
}

/** Triggers a browser "Save As" download for an already-fetched blob. */
export function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
