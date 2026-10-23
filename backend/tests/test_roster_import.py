
import csv

import pytest

from app import db
from app.models import RosterRecord
from app.services.roster_import import import_roster_csv


def write_csv(path, rows):
    columns = [
        "college_id_number",
        "official_name",
        "official_role",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    return str(path)


def test_import_valid_roster(app, tmp_path):
    csv_path = write_csv(
        tmp_path / "roster.csv",
        [
            {
                "college_id_number": "TEST001",
                "official_name": "Sample Student",
                "official_role": "student",
            },
            {
                "college_id_number": "TEST002",
                "official_name": "Sample Faculty",
                "official_role": "faculty",
            },
        ],
    )

    with app.app_context():
        count = import_roster_csv(csv_path)

        assert count == 2
        assert db.session.query(RosterRecord).count() == 2


def test_invalid_role_is_rejected_without_partial_import(app, tmp_path):
    csv_path = write_csv(
        tmp_path / "roster.csv",
        [
            {
                "college_id_number": "TEST001",
                "official_name": "Sample Student",
                "official_role": "student",
            },
            {
                "college_id_number": "TEST002",
                "official_name": "Sample Person",
                "official_role": "admin",
            },
        ],
    )

    with app.app_context():
        with pytest.raises(ValueError, match="unsupported official role"):
            import_roster_csv(csv_path)

        assert db.session.query(RosterRecord).count() == 0


def test_duplicate_ids_in_csv_are_rejected(app, tmp_path):
    csv_path = write_csv(
        tmp_path / "roster.csv",
        [
            {
                "college_id_number": "TEST001",
                "official_name": "Sample Student",
                "official_role": "student",
            },
            {
                "college_id_number": "test001",
                "official_name": "Another Student",
                "official_role": "student",
            },
        ],
    )

    with app.app_context():
        with pytest.raises(ValueError, match="duplicate college ID"):
            import_roster_csv(csv_path)

        assert db.session.query(RosterRecord).count() == 0


def test_existing_roster_id_is_not_overwritten(app, tmp_path):
    existing = RosterRecord(
        college_id_number="TEST001",
        official_name="Original Name",
        official_role="student",
    )

    csv_path = write_csv(
        tmp_path / "roster.csv",
        [
            {
                "college_id_number": "TEST001",
                "official_name": "Changed Name",
                "official_role": "faculty",
            },
        ],
    )

    with app.app_context():
        db.session.add(existing)
        db.session.commit()

        with pytest.raises(ValueError, match="already exist"):
            import_roster_csv(csv_path)

        record = db.session.execute(
            db.select(RosterRecord).where(
                RosterRecord.college_id_number == "TEST001"
            )
        ).scalar_one()

        assert record.official_name == "Original Name"
        assert record.official_role == "student"
