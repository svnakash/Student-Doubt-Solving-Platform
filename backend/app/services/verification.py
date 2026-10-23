
from app import db
from app.models import User, VerificationAttempt
from app.services.roster import match_roster_record


MAX_VERIFICATION_ATTEMPTS = 3


def get_attempt_count(user_id: int) -> int:
    """Return the number of recorded verification attempts."""
    return db.session.execute(
        db.select(db.func.count(VerificationAttempt.id)).where(
            VerificationAttempt.user_id == user_id
        )
    ).scalar_one()


def _verify_user_against_roster(
    user_id: int,
    college_id_number: str,
    extracted_name: str,
) -> dict:
    user = db.session.execute(
        db.select(User)
        .where(User.id == user_id)
        .with_for_update()
    ).scalar_one_or_none()

    if user is None or not user.is_active:
        return {
            "success": False,
            "code": "USER_NOT_AVAILABLE",
            "message": "This account is unavailable.",
        }

    if user.verification_status == "verified":
        return {
            "success": True,
            "code": "ALREADY_VERIFIED",
            "verification_status": "verified",
            "role": user.role,
        }

    attempt_count = get_attempt_count(user_id)

    if attempt_count >= MAX_VERIFICATION_ATTEMPTS:
        return {
            "success": False,
            "code": "RETRY_LIMIT_REACHED",
            "message": "Please contact the college office for assistance.",
        }

    record = match_roster_record(
        college_id_number=college_id_number,
        extracted_name=extracted_name,
    )

    if record is None:
        db.session.add(
            VerificationAttempt(
                user_id=user.id,
                status="failed",
                failure_code="ROSTER_MISMATCH",
            )
        )
        user.verification_status = "verification_retry_required"
        db.session.commit()

        return {
            "success": False,
            "code": "ROSTER_MISMATCH",
            "verification_status": user.verification_status,
            "attempts_remaining": MAX_VERIFICATION_ATTEMPTS
            - attempt_count
            - 1,
            "message": (
                "The details could not be matched. "
                "Please check them and retry."
            ),
        }

    user.role = record.official_role
    user.verification_status = "verified"

    db.session.add(
        VerificationAttempt(
            user_id=user.id,
            status="succeeded",
            failure_code=None,
        )
    )
    db.session.commit()

    return {
        "success": True,
        "code": "VERIFIED",
        "verification_status": "verified",
        "role": user.role,
        "attempts_remaining": MAX_VERIFICATION_ATTEMPTS
        - attempt_count
        - 1,
    }


def verify_user_against_roster(
    user_id: int,
    college_id_number: str,
    extracted_name: str,
) -> dict:
    """Verify against the official roster and rollback on database errors."""
    try:
        return _verify_user_against_roster(
            user_id=user_id,
            college_id_number=college_id_number,
            extracted_name=extracted_name,
        )
    except Exception:
        db.session.rollback()
        raise
