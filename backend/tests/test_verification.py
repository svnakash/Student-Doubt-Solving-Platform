
from app import db
from app.models import User, RosterRecord, VerificationAttempt
from app.services.verification import verify_user_against_roster


def create_user():
    user = User(
        name="Test Student",
        email="student@example.com",
        password_hash="test-hash",
        role="student",
        verification_status="pending_verification",
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_roster_record():
    record = RosterRecord(
        college_id_number="TEST001",
        official_name="Test Student",
        official_role="student",
        is_active=True,
    )
    db.session.add(record)
    db.session.commit()
    return record


def test_successful_match_verifies_user(app):
    with app.app_context():
        user = create_user()
        create_roster_record()

        result = verify_user_against_roster(
            user.id,
            "TEST001",
            "Test Student",
        )

        db.session.refresh(user)
        assert result["success"] is True
        assert user.verification_status == "verified"
        assert user.role == "student"


def test_failed_match_does_not_verify_user(app):
    with app.app_context():
        user = create_user()

        result = verify_user_against_roster(
            user.id,
            "UNKNOWN001",
            "Unknown Person",
        )

        db.session.refresh(user)
        assert result["success"] is False
        assert user.verification_status == "verification_retry_required"
        assert user.role == "student"


def test_three_failed_attempts_reach_retry_limit(app):
    with app.app_context():
        user = create_user()

        for _ in range(3):
            verify_user_against_roster(
                user.id,
                "UNKNOWN001",
                "Unknown Person",
            )

        result = verify_user_against_roster(
            user.id,
            "UNKNOWN001",
            "Unknown Person",
        )

        assert result["code"] == "RETRY_LIMIT_REACHED"
        assert db.session.query(VerificationAttempt).filter_by(
            user_id=user.id
        ).count() == 3


def test_faculty_role_comes_from_official_roster(app):
    with app.app_context():
        user = create_user()

        record = RosterRecord(
            college_id_number="FAC001",
            official_name="Test Student",
            official_role="faculty",
            is_active=True,
        )
        db.session.add(record)
        db.session.commit()

        result = verify_user_against_roster(
            user.id,
            "FAC001",
            "Test Student",
        )

        db.session.refresh(user)
        assert result["success"] is True
        assert user.role == "faculty"
        assert user.verification_status == "verified"

def test_inactive_user_cannot_be_verified(app):
    with app.app_context():
        user = create_user()
        user.is_active = False
        db.session.commit()

        create_roster_record()

        result = verify_user_against_roster(
            user.id,
            "TEST001",
            "Test Student",
        )

        db.session.refresh(user)

        assert result["code"] == "USER_NOT_AVAILABLE"
        assert user.verification_status == "pending_verification"
        assert user.role == "student"
        assert db.session.query(VerificationAttempt).filter_by(
            user_id=user.id
        ).count() == 0


def test_already_verified_user_role_is_not_overwritten(app):
    with app.app_context():
        user = create_user()
        user.verification_status = "verified"
        user.role = "student"

        db.session.add(
            RosterRecord(
                college_id_number="FAC001",
                official_name="Test Student",
                official_role="faculty",
                is_active=True,
            )
        )
        db.session.commit()

        result = verify_user_against_roster(
            user.id,
            "FAC001",
            "Test Student",
        )

        db.session.refresh(user)

        assert result["code"] == "ALREADY_VERIFIED"
        assert user.role == "student"
        assert user.verification_status == "verified"
