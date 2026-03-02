"""
Tests for the Mergington High School API endpoints.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture()
def client():
    """Yield a TestClient and reset the in-memory activities after each test."""
    original = copy.deepcopy(activities)
    with TestClient(app) as c:
        yield c
    # Restore original state so tests don't leak mutations
    activities.clear()
    activities.update(original)


# ── GET / ────────────────────────────────────────────────────────────────────

def test_root_redirects(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ── GET /activities ──────────────────────────────────────────────────────────

def test_get_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 9

    for name, details in data.items():
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)


# ── POST /activities/{name}/signup ───────────────────────────────────────────

def test_signup_success(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]

    # Verify the participant now appears in the activity
    activities_resp = client.get("/activities")
    participants = activities_resp.json()["Chess Club"]["participants"]
    assert "newstudent@mergington.edu" in participants


def test_signup_duplicate(client):
    # michael@ is already in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_activity_not_found(client):
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ── DELETE /activities/{name}/signup ─────────────────────────────────────────

def test_unregister_success(client):
    # michael@ is pre-registered in Chess Club
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]

    # Verify the participant was removed
    activities_resp = client.get("/activities")
    participants = activities_resp.json()["Chess Club"]["participants"]
    assert "michael@mergington.edu" not in participants


def test_unregister_not_signed_up(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "nobody@mergington.edu"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_activity_not_found(client):
    response = client.delete(
        "/activities/Nonexistent Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
