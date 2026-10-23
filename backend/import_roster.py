
import argparse
import sys

from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.services.roster_import import import_roster_csv


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Import an authorized college roster from a CSV file."
    )
    parser.add_argument(
        "csv_file",
        help="Path to the authorized roster CSV file.",
    )
    args = parser.parse_args(argv)

    app = create_app()

    try:
        with app.app_context():
            count = import_roster_csv(args.csv_file)

        print(f"Roster import successful. Records imported: {count}")
        return 0

    except ValueError as exc:
        print(f"Roster import rejected: {exc}", file=sys.stderr)
        return 1

    except OSError:
        print(
            "Roster import failed: the CSV file could not be accessed.",
            file=sys.stderr,
        )
        return 1

    except SQLAlchemyError:
        print(
            "Roster import failed because of a database error.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
