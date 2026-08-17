import React, { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Users, Activity, Video as VideoIcon, ShieldAlert } from "lucide-react";
import { api } from "../api";
import { formatIST } from "../utils";
import PoseLoader from "../components/PoseLoader";

const ROLE_COLORS = {
  athlete: "#3A36E0",
  coach: "#FF6B35",
  physiotherapist: "#1E9E5A",
  admin: "#D69A00",
};

function roleColor(role, idx) {
  return ROLE_COLORS[role] || ["#3A36E0", "#FF6B35", "#1E9E5A", "#D69A00", "#8B94A3"][idx % 5];
}

export default function AdminDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [togglingId, setTogglingId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [d, u] = await Promise.all([api.getAdminDashboard(), api.listAllUsers()]);
      setDashboard(d);
      setUsers(u);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleToggle = async (userId) => {
    setTogglingId(userId);
    setError("");
    try {
      await api.toggleUserActive(userId);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setTogglingId(null);
    }
  };

  if (loading) return <div className="page"><PoseLoader text="Loading platform analytics..." /></div>;
  if (error && !dashboard) return <div className="page"><p className="error">{error}</p></div>;
  if (!dashboard) return null;

  const usersByRolePie = dashboard.users_by_role.map((r) => ({ name: r.role, value: r.count }));
  const loginsByRolePie = dashboard.logins_by_role.map((r) => ({ name: r.role, value: r.count }));

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>Admin Dashboard</h2>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="stat-grid">
        <div className="stat-card">
          <Users size={20} strokeWidth={2} />
          <div>
            <p className="stat-value">{dashboard.total_users}</p>
            <p className="stat-label">Total Users ({dashboard.active_users} active, {dashboard.inactive_users} inactive)</p>
          </div>
        </div>
        <div className="stat-card">
          <Activity size={20} strokeWidth={2} />
          <div>
            <p className="stat-value">{dashboard.total_athletes}</p>
            <p className="stat-label">Athlete Profiles</p>
          </div>
        </div>
        <div className="stat-card">
          <VideoIcon size={20} strokeWidth={2} />
          <div>
            <p className="stat-value">{dashboard.total_videos}</p>
            <p className="stat-label">Videos Uploaded ({dashboard.total_processed_reports} analyzed)</p>
          </div>
        </div>
        <div className="stat-card">
          <ShieldAlert size={20} strokeWidth={2} />
          <div>
            <p className="stat-value">{dashboard.high_risk_video_count}</p>
            <p className="stat-label">High / Critical Risk Reports</p>
          </div>
        </div>
      </div>

      <div className="chart-grid">
        <div className="card">
          <h3>Registered Users by Role</h3>
          <p className="muted" style={{ marginTop: -6 }}>{dashboard.total_users} total accounts</p>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={usersByRolePie}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={95}
                label={({ name, value }) => `${name}: ${value}`}
              >
                {usersByRolePie.map((entry, idx) => (
                  <Cell key={idx} fill={roleColor(entry.name, idx)} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Logins by Role</h3>
          <p className="muted" style={{ marginTop: -6 }}>{dashboard.total_logins} total logins recorded</p>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={loginsByRolePie}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={95}
                label={({ name, value }) => `${name}: ${value}`}
              >
                {loginsByRolePie.map((entry, idx) => (
                  <Cell key={idx} fill={roleColor(entry.name, idx)} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>User Management</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th><th>Email</th><th>Role</th><th>Status</th>
              <th>Logins</th><th>Last Login</th><th>Joined</th><th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>
                  <span className={`badge ${u.is_active ? "badge-success" : "badge-danger"}`}>
                    {u.is_active ? "Active" : "Deactivated"}
                  </span>
                </td>
                <td>{u.login_count}</td>
                <td>{u.last_login_at ? formatIST(u.last_login_at) : "Never"}</td>
                <td>{formatIST(u.created_at, { withTime: false })}</td>
                <td className="table-actions">
                  <button
                    onClick={() => handleToggle(u.id)}
                    disabled={togglingId === u.id}
                  >
                    {togglingId === u.id ? "..." : u.is_active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {dashboard.recent_users.length > 0 && (
        <div className="card">
          <h3>Recently Registered</h3>
          <table className="table">
            <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead>
            <tbody>
              {dashboard.recent_users.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>{u.role}</td>
                  <td>{formatIST(u.created_at, { withTime: false })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
