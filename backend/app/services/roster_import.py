
import csv

from app import db
from app.models import RosterRecord
from app.services.roster import (
    normalize_college_id,
    normalize_person_name,
)


REQUIRED_COLUMNS = {
    "college_id_number",
    "official_name",
    "official_role",
}


def import_roster_csv(file_path: str) -> int:
    """
    Validate and import a CSV roster.

    Existing roster IDs are rejected rather than silently overwritten.
    The transaction is rolled back if validation or insertion fails.
    """
    with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(
            set(reader.fieldnames)
        ):
            raise ValueError("CSV is missing required columns.")

        rows = []
        seen_ids = set()

        for row_number, row in enumerate(reader, start=2):
            college_id = normalize_college_id(
                row.get("college_id_number") or ""
            )
            official_name = " ".join(
                (row.get("official_name") or "").split()
            )
            official_role = (row.get("official_role") or "").strip().lower()

            if not college_id or not official_name:
                raise ValueError(
                    f"Row {row_number}: college ID and name are required."
                )

            if len(college_id) > 100 or len(official_name) > 120:
                raise ValueError(
                    f"Row {row_number}: a field exceeds its allowed length."
                )

            if official_role not in {"student", "faculty"}:
                raise ValueError(
                    f"Row {row_number}: unsupported official role."
                )

            if college_id in seen_ids:
                raise ValueError(
                    f"Row {row_number}: duplicate college ID in CSV."
                )

            seen_ids.add(college_id)

            rows.append({
                "college_id_number": college_id,
                "official_name": official_name,
                "official_role": official_role,
            })

    if not rows:
        raise ValueError("CSV contains no roster records.")

    try:
        existing_ids = {
            value
            for (value,) in db.session.execute(
                db.select(RosterRecord.college_id_number).where(
                    RosterRecord.college_id_number.in_(seen_ids)
                )
            ).all()
        }

        if existing_ids:
            raise ValueError(
                "One or more college IDs already exist in the roster."
            )

        db.session.add_all(
            RosterRecord(**row)
            for row in rows
        )
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return len(rows)
