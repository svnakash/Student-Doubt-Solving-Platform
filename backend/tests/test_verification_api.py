
def register_and_login(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Student",
            "email": "student@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert login_response.status_code == 200

    return login_response.get_json()["data"]["access_token"]


def test_verification_endpoint_requires_token(client):
    response = client.post(
        "/api/v1/verification/verify-details",
        json={
            "college_id_number": "TEST001",
            "name": "Test Student",
        },
    )

    assert response.status_code == 401


def test_verification_endpoint_is_disabled(client):
    token = register_and_login(client)

    response = client.post(
        "/api/v1/verification/verify-details",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "college_id_number": "TEST001",
            "name": "Test Student",
        },
    )

    assert response.status_code == 501

    body = response.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == "VERIFICATION_UPLOAD_REQUIRED"


def test_disabled_endpoint_cannot_verify_user(client):
    token = register_and_login(client)

    response = client.post(
        "/api/v1/verification/verify-details",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "college_id_number": "TEST001",
            "name": "Test Student",
        },
    )

    assert response.status_code == 501

    status_response = client.get(
        "/api/v1/auth/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert status_response.status_code == 200
    assert (
        status_response.get_json()["data"]["verification_status"]
        == "pending_verification"
    )
