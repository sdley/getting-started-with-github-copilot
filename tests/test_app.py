import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    # Keep a deep copy of the activities and restore after each test
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = original


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # ensure some known activity exists
    assert "Soccer Team" in data


def test_signup_and_unregister_flow(client):
    activity = "Chess Club"
    email = "tester@example.com"

    # Sign up
    resp = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Verify participant present
    resp = client.get("/activities")
    participants = resp.json()[activity]["participants"]
    assert email in participants

    # Unregister
    resp = client.delete(f"/activities/{quote(activity)}/signup", params={"email": email})
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Verify removed
    resp = client.get("/activities")
    participants = resp.json()[activity]["participants"]
    assert email not in participants


def test_signup_existing_fails(client):
    activity = "Soccer Team"
    existing = "alex@mergington.edu"

    resp = client.post(f"/activities/{quote(activity)}/signup", params={"email": existing})
    assert resp.status_code == 400


def test_unregister_not_signed_up_fails(client):
    activity = "Art Club"
    email = "not-signed-up@example.com"

    resp = client.delete(f"/activities/{quote(activity)}/signup", params={"email": email})
    assert resp.status_code == 400


def test_activity_not_found(client):
    bogus = "Nonexistent Activity"
    resp = client.post(f"/activities/{quote(bogus)}/signup", params={"email": "a@b.com"})
    assert resp.status_code == 404

    resp = client.delete(f"/activities/{quote(bogus)}/signup", params={"email": "a@b.com"})
    assert resp.status_code == 404
