from .conftest import register_and_login


def test_register_and_login(client):
    res = client.post("/auth/register", json={
        "full_name": "Jane Coach", "email": "jane@example.com",
        "password": "secret123", "role": "coach",
    })
    assert res.status_code == 201
    assert res.json()["email"] == "jane@example.com"

    res = client.post("/auth/login", data={"username": "jane@example.com", "password": "secret123"})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["role"] == "coach"


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={
        "full_name": "Jane Coach", "email": "jane2@example.com",
        "password": "secret123", "role": "coach",
    })
    res = client.post("/auth/login", data={"username": "jane2@example.com", "password": "wrong"})
    assert res.status_code == 401


def test_duplicate_email_rejected(client):
    payload = {"full_name": "Dup", "email": "dup@example.com", "password": "secret123", "role": "athlete"}
    r1 = client.post("/auth/register", json=payload)
    r2 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 400


def test_sports_scientist_role_no_longer_accepted(client):
    """Sports Scientist role was removed — registering with it should fail validation."""
    res = client.post("/auth/register", json={
        "full_name": "Old Role", "email": "old@example.com",
        "password": "secret123", "role": "sports_scientist",
    })
    assert res.status_code == 422


def test_protected_endpoint_requires_auth(client):
    res = client.get("/athletes/")
    assert res.status_code == 401


def test_athlete_cannot_create_athlete_for_someone_else(client):
    headers = register_and_login(client, "athlete1@example.com", role="athlete")
    res = client.post("/athletes/", json={
        "athlete_code": "ATH-X", "sport_type": "Soccer", "age": 20,
        "height_cm": 180, "weight_kg": 75,
    }, headers=headers)
    assert res.status_code == 403


def test_coach_can_create_athlete(client):
    headers = register_and_login(client, "coach1@example.com", role="coach")
    res = client.post("/athletes/", json={
        "athlete_code": "ATH-100", "sport_type": "Soccer", "age": 20,
        "height_cm": 180, "weight_kg": 75,
    }, headers=headers)
    assert res.status_code == 201
    assert res.json()["athlete_code"] == "ATH-100"
