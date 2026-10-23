
from app import db
from app.models import RosterRecord
from app.services.roster import (
    match_roster_record,
    normalize_college_id,
    normalize_person_name,
)


def add_roster_record(
    college_id="COLL001",
    name="Test Student",
    role="student",
    active=True,
):
    record = RosterRecord(
        college_id_number=college_id,
        official_name=name,
        official_role=role,
        is_active=active,
    )
    db.session.add(record)
    db.session.commit()
    return record


def test_college_id_normalization():
    assert normalize_college_id(" coll001 ") == "COLL001"


def test_person_name_normalization():
    assert normalize_person_name("  TEST   Student ") == "test student"


def test_matching_roster_record_succeeds(app):
    with app.app_context():
        add_roster_record()

        record = match_roster_record(" coll001 ", "  TEST   Student ")

        assert record is not None
        assert record.college_id_number == "COLL001"
        assert record.official_role == "student"


def test_wrong_name_is_rejected(app):
    with app.app_context():
        add_roster_record()

        record = match_roster_record("COLL001", "Different Person")

        assert record is None


def test_unknown_or_inactive_roster_record_is_rejected(app):
    with app.app_context():
        add_roster_record(college_id="INACTIVE001", active=False)

        assert match_roster_record("UNKNOWN001", "Test Student") is None
        assert match_roster_record("INACTIVE001", "Test Student") is None


def test_roster_role_is_taken_from_official_record(app):
    with app.app_context():
        add_roster_record(
            college_id="FAC001",
            name="Test Faculty",
            role="faculty",
        )

        record = match_roster_record("FAC001", "Test Faculty")

        assert record is not None
        assert record.official_role == "faculty"


def test_empty_or_invalid_inputs_are_rejected(app):
    with app.app_context():
        assert match_roster_record("", "Test Student") is None
        assert match_roster_record("COLL001", "") is None
        assert match_roster_record(None, "Test Student") is None
