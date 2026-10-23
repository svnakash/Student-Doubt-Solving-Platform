
import re

from app import db
from app.models import RosterRecord


def normalize_college_id(college_id_number: str) -> str:
    """Normalize an extracted college ID for matching."""
    return college_id_number.strip().upper()


def normalize_person_name(name: str) -> str:
    """Normalize whitespace and casing for name comparison."""
    return " ".join(name.strip().lower().split())


def match_roster_record(
    college_id_number: str,
    extracted_name: str,
):
    """
    Return an active official roster record when both ID and name match.

    The returned role comes from the trusted roster, never from user input.
    """
    if not isinstance(college_id_number, str):
        return None

    if not isinstance(extracted_name, str):
        return None

    normalized_id = normalize_college_id(college_id_number)
    normalized_name = normalize_person_name(extracted_name)

    if not normalized_id or not normalized_name:
        return None

    record = db.session.execute(
        db.select(RosterRecord).where(
            RosterRecord.college_id_number == normalized_id,
            RosterRecord.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if record is None:
        return None

    if normalize_person_name(record.official_name) != normalized_name:
        return None

    if record.official_role not in {"student", "faculty"}:
        return None

    return record
