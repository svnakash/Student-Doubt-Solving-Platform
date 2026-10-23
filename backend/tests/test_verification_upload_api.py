
from io import BytesIO
from unittest.mock import patch

from flask_jwt_extended import create_access_token

from app import db
from app.models import RosterRecord, User
from app.models import User


def create_verified_test_token(app, user_id):
    with app.app_context():
        return create_access_token(identity=str(user_id))


def create_test_user(app, client):
    with app.app_context():
        user = User(
            name="Test Student",
            email="upload-test@example.com",
            password_hash="test-hash",
            role="student",
            verification_status="pending_verification",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    token = create_verified_test_token(app, user_id)
    return user_id, {"Authorization": f"Bearer {token}"}


def test_upload_requires_authentication(client):
    response = client.post("/api/v1/verification/upload")

    assert response.status_code == 401


def test_upload_requires_id_card(app, client):
    _, headers = create_test_user(app, client)

    response = client.post(
        "/api/v1/verification/upload",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "IMAGE_REQUIRED"


def test_invalid_image_is_rejected(app, client):
    _, headers = create_test_user(app, client)

    response = client.post(
        "/api/v1/verification/upload",
        headers=headers,
        data={"id_card": (BytesIO(b"not an image"), "card.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "INVALID_IMAGE"


def test_ocr_failure_does_not_verify_user(app, client):
    user_id, headers = create_test_user(app, client)

    with patch(
        "app.routes.verification.validate_id_card_image",
        return_value=(True, None),
    ), patch(
        "app.routes.verification.temporary_image_copy"
    ) as temporary_copy, patch(
        "app.routes.verification.extract_text_from_image",
        side_effect=RuntimeError("simulated OCR failure"),
    ):
        from contextlib import contextmanager
        from pathlib import Path

        @contextmanager
        def fake_temporary_copy(_uploaded_file):
            yield Path("fake-id-card.png")

        temporary_copy.side_effect = fake_temporary_copy

        response = client.post(
            "/api/v1/verification/upload",
            headers=headers,
            data={"id_card": (BytesIO(b"image bytes"), "card.png")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 503
    assert response.json["error"]["code"] == "OCR_UNAVAILABLE"

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.verification_status == "pending_verification"

from contextlib import contextmanager
from pathlib import Path


def add_roster_record(app, college_id, official_name, official_role):
    with app.app_context():
        record = RosterRecord(
            college_id_number=college_id,
            official_name=official_name,
            official_role=official_role,
            is_active=True,
        )
        db.session.add(record)
        db.session.commit()


@contextmanager
def fake_temporary_image(_uploaded_file):
    # No real ID image is written to disk in these tests.
    yield Path("mock-id-card.png")


def post_mocked_id_card(client, headers, ocr_text):
    with patch(
        "app.routes.verification.validate_id_card_image",
        return_value=(True, None),
    ), patch(
        "app.routes.verification.temporary_image_copy",
        side_effect=fake_temporary_image,
    ), patch(
        "app.routes.verification.extract_text_from_image",
        return_value=ocr_text,
    ):
        return client.post(
            "/api/v1/verification/upload",
            headers=headers,
            data={
                "id_card": (
                    BytesIO(b"mock image bytes"),
                    "card.png",
                )
            },
            content_type="multipart/form-data",
        )


def test_matching_roster_record_verifies_user_and_assigns_official_role(
    app, client
):
    user_id, headers = create_test_user(app, client)
    add_roster_record(
        app,
        college_id="FAC-1001",
        official_name="Official Faculty",
        official_role="faculty",
    )

    response = post_mocked_id_card(
        client,
        headers,
        "Name: Official Faculty\nCollege ID: FAC-1001",
    )

    assert response.status_code == 200
    assert response.json["data"]["verification_status"] == "verified"
    assert response.json["data"]["role"] == "faculty"

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.verification_status == "verified"
        assert user.role == "faculty"


def test_roster_name_mismatch_does_not_grant_faculty_role(app, client):
    user_id, headers = create_test_user(app, client)
    add_roster_record(
        app,
        college_id="FAC-1002",
        official_name="Official Faculty",
        official_role="faculty",
    )

    response = post_mocked_id_card(
        client,
        headers,
        "Name: Test Student\nCollege ID: FAC-1002",
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "ROSTER_MISMATCH"

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.verification_status == "verification_retry_required"
        assert user.role == "student"

def test_upload_rate_limit_returns_429(app, client):
    # The upload route's rate limiter runs before JWT authentication,
    # so unauthenticated requests can test the limit without creating users.
    responses = [
        client.post("/api/v1/verification/upload")
        for _ in range(11)
    ]

    assert all(response.status_code == 401 for response in responses[:10])
    assert responses[10].status_code == 429
