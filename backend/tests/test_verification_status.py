
def create_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Student",
            "email": "student@example.com",
            "password": "Strong-Password-123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            "password": "Strong-Password-123!",
        },
    )

    assert response.status_code == 200
    return response.get_json()["data"]["access_token"]


def test_status_requires_authentication(client):
    response = client.get("/api/v1/auth/status")

    assert response.status_code == 401


def test_status_reports_pending_verification(client):
    token = create_token(client)

    response = client.get(
        "/api/v1/auth/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["verification_status"] == "pending_verification"
    assert data["is_verified"] is False
    assert data["role"] == "student"
