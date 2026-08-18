from .conftest import register_and_login


def test_risk_assessment_with_no_videos(client):
    headers = register_and_login(client, "coach2@example.com", role="coach")
    res = client.post("/athletes/", json={
        "athlete_code": "ATH-200", "sport_type": "Basketball", "age": 24,
        "height_cm": 190, "weight_kg": 85,
    }, headers=headers)
    athlete_id = res.json()["id"]

    res = client.get(f"/athletes/{athlete_id}/risk-assessment", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["video_count"] == 0
    assert body["overall_score"] is None
    assert "No completed video reports" in body["message"]


def test_admin_dashboard_requires_admin_role(client):
    coach_headers = register_and_login(client, "coach3@example.com", role="coach")
    res = client.get("/admin/dashboard", headers=coach_headers)
    assert res.status_code == 403


def test_admin_dashboard_counts_users_and_logins(client):
    # Register a few users of different roles and log some of them in more than once
    register_and_login(client, "athlete_x@example.com", role="athlete")
    register_and_login(client, "coach_x@example.com", role="coach")
    admin_headers = register_and_login(client, "admin_x@example.com", role="admin")
    # log the admin in again to bump login_count
    client.post("/auth/login", data={"username": "admin_x@example.com", "password": "testpass123"})

    res = client.get("/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total_users"] >= 3
    role_names = {rc["role"] for rc in body["users_by_role"]}
    assert "athlete" in role_names and "coach" in role_names and "admin" in role_names
    assert "sports_scientist" not in role_names
    assert body["total_logins"] >= 3


def test_admin_can_toggle_user_active_state(client):
    admin_headers = register_and_login(client, "admin_y@example.com", role="admin")
    res = client.post("/auth/register", json={
        "full_name": "Toggle Me", "email": "toggle@example.com",
        "password": "secret123", "role": "athlete",
    })
    user_id = res.json()["id"]

    res = client.put(f"/admin/users/{user_id}/toggle-active", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Deactivated user can no longer log in
    res = client.post("/auth/login", data={"username": "toggle@example.com", "password": "secret123"})
    assert res.status_code == 403


def test_team_overview_accessible_to_coach_not_athlete(client):
    coach_headers = register_and_login(client, "coach4@example.com", role="coach")
    athlete_headers = register_and_login(client, "athlete4@example.com", role="athlete")

    res = client.get("/athletes/team/overview", headers=coach_headers)
    assert res.status_code == 200

    res = client.get("/athletes/team/overview", headers=athlete_headers)
    assert res.status_code == 403
