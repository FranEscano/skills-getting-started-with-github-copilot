import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


TEST_ACTIVITY = "Basketball Club"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        name: activity["participants"].copy()
        for name, activity in activities.items()
    }

    yield

    for name, participants in original_participants.items():
        activities[name]["participants"][:] = participants


def test_get_activities_returns_current_data_without_caching(client):
    # Arrange
    expected_activities = activities.copy()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {TEST_ACTIVITY}"}
    assert email in activities[TEST_ACTIVITY]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "already.signed.up@mergington.edu"
    activities[TEST_ACTIVITY]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities[TEST_ACTIVITY]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    email = "registered.student@mergington.edu"
    activities[TEST_ACTIVITY]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {TEST_ACTIVITY}"}
    assert email not in activities[TEST_ACTIVITY]["participants"]


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "registered.student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
