
from app import db
from app.models import User
from app.services.security import verify_password


def test_register_creates_pending_student_account(client, app):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Student",
            "email": "Student@Example.com",
            "password": "Strong-Password-123!",
            "role": "faculty",
        },
    )

    assert response.status_code == 201

    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["email"] == "student@example.com"
    assert body["data"]["role"] == "student"
    assert body["data"]["verification_status"] == "pending_verification"
    assert "password" not in body["data"]
    assert "password_hash" not in body["data"]

    with app.app_context():
        user = db.session.get(User, body["data"]["id"])

        assert user is not None
        assert user.password_hash != "Strong-Password-123!"
        assert verify_password(
            "Strong-Password-123!",
            user.password_hash,
        )


def test_register_rejects_duplicate_email(client):
    payload = {
        "name": "Test Student",
        "email": "student@example.com",
        "password": "Strong-Password-123!",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )
    second_response = client.post(
        "/api/v1/auth/register",
        json={
            **payload,
            "email": " Student@Example.com ",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Student",
            "email": "student@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 400
    assert "password" in response.get_json()["error"]["details"]


def test_register_rejects_missing_json(client):
    response = client.post(
        "/api/v1/auth/register",
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_JSON"
