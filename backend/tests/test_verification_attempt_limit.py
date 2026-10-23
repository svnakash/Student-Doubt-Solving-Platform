
from app import db
from app.models import User, VerificationAttempt
from app.services.verification import (
    MAX_VERIFICATION_ATTEMPTS,
    verify_user_against_roster,
)


def create_pending_user():
    user = User(
        name="Test Student",
        email="attempt-limit@example.com",
        password_hash="test-hash",
        role="student",
        verification_status="verification_retry_required",
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_attempt_limit_is_three():
    assert MAX_VERIFICATION_ATTEMPTS == 3


def test_user_with_three_failed_attempts_cannot_try_again(app):
    with app.app_context():
        user = create_pending_user()
        user_id = user.id

        for _ in range(MAX_VERIFICATION_ATTEMPTS):
            db.session.add(
                VerificationAttempt(
                    user_id=user_id,
                    status="failed",
                    failure_code="ROSTER_MISMATCH",
                )
            )
        db.session.commit()

        result = verify_user_against_roster(
            user_id=user_id,
            college_id_number="FAC-9999",
            extracted_name="Unknown Person",
        )

        assert result["success"] is False
        assert result["code"] == "RETRY_LIMIT_REACHED"

        attempts = db.session.execute(
            db.select(db.func.count(VerificationAttempt.id)).where(
                VerificationAttempt.user_id == user_id
            )
        ).scalar_one()

        assert attempts == MAX_VERIFICATION_ATTEMPTS

        refreshed_user = db.session.get(User, user_id)
        assert refreshed_user.role == "student"
        assert refreshed_user.verification_status == "verification_retry_required"


def test_user_with_fewer_than_three_attempts_can_be_checked(app):
    with app.app_context():
        user = create_pending_user()
        user_id = user.id

        for _ in range(MAX_VERIFICATION_ATTEMPTS - 1):
            db.session.add(
                VerificationAttempt(
                    user_id=user_id,
                    status="failed",
                    failure_code="ROSTER_MISMATCH",
                )
            )
        db.session.commit()

        result = verify_user_against_roster(
            user_id=user_id,
            college_id_number="UNKNOWN-001",
            extracted_name="Unknown Person",
        )

        assert result["success"] is False
        assert result["code"] == "ROSTER_MISMATCH"
        assert result["attempts_remaining"] == 0

        attempts = db.session.execute(
            db.select(db.func.count(VerificationAttempt.id)).where(
                VerificationAttempt.user_id == user_id
            )
        ).scalar_one()

        assert attempts == MAX_VERIFICATION_ATTEMPTS
