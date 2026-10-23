
from app.services.identity_parser import parse_identity_fields


def test_parses_labeled_identity_fields():
    text = """
    ABC Engineering College
    Name: Ravi Kumar
    College ID: STU2026001
    """

    result = parse_identity_fields(text)

    assert result["name"] == "Ravi Kumar"
    assert result["college_id_number"] == "STU2026001"
    assert result["college_name"] == "ABC Engineering College"


def test_parses_id_number_label():
    result = parse_identity_fields(
        "Name: Priya Devi\nID Number: FAC-1024"
    )

    assert result["name"] == "Priya Devi"
    assert result["college_id_number"] == "FAC-1024"


def test_empty_text_returns_empty_fields():
    result = parse_identity_fields("  ")

    assert result == {
        "college_id_number": None,
        "name": None,
        "college_name": None,
    }


def test_unlabeled_text_does_not_guess_name_or_id():
    result = parse_identity_fields(
        "Ravi Kumar\nSTU2026001\nABC Engineering College"
    )

    assert result["name"] is None
    assert result["college_id_number"] is None
    assert result["college_name"] == "ABC Engineering College"


def test_non_string_input_is_handled():
    result = parse_identity_fields(None)

    assert result["name"] is None
    assert result["college_id_number"] is None
    assert result["college_name"] is None
