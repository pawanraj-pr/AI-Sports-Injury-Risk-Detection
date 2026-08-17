from .conftest import register_and_login


def test_athlete_self_profile_flow(client):
    headers = register_and_login(client, "selfserve@example.com", role="athlete")

    # No profile yet
    res = client.get("/athletes/me", headers=headers)
    assert res.status_code == 404

    # Create own profile
    res = client.post("/athletes/me", json={
        "athlete_code": "ATH-SELF-1", "sport_type": "Running", "age": 25,
        "height_cm": 175, "weight_kg": 68,
    }, headers=headers)
    assert res.status_code == 201
    athlete_id = res.json()["id"]

    # Fetch it back
    res = client.get("/athletes/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["athlete_code"] == "ATH-SELF-1"

    # Can't create a second profile
    res = client.post("/athletes/me", json={
        "athlete_code": "ATH-SELF-2", "sport_type": "Running", "age": 25,
        "height_cm": 175, "weight_kg": 68,
    }, headers=headers)
    assert res.status_code == 400

    # Can update own profile
    res = client.put("/athletes/me", json={"age": 26}, headers=headers)
    assert res.status_code == 200
    assert res.json()["age"] == 26

    # Only ever sees own athlete in the list
    res = client.get("/athletes/", headers=headers)
    assert res.status_code == 200
    ids = [a["id"] for a in res.json()]
    assert ids == [athlete_id]


def test_athlete_cannot_view_another_athletes_profile(client):
    headers1 = register_and_login(client, "athleteA@example.com", role="athlete")
    headers2 = register_and_login(client, "athleteB@example.com", role="athlete")

    client.post("/athletes/me", json={
        "athlete_code": "ATH-A", "sport_type": "Soccer", "age": 22,
        "height_cm": 178, "weight_kg": 74,
    }, headers=headers1)

    coach_headers = register_and_login(client, "coachX@example.com", role="coach")
    all_athletes = client.get("/athletes/", headers=coach_headers).json()
    other_id = [a["id"] for a in all_athletes if a["athlete_code"] == "ATH-A"][0]

    res = client.get(f"/athletes/{other_id}", headers=headers2)
    assert res.status_code == 403
