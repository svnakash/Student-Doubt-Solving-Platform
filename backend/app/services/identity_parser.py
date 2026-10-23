
import re


ID_LABEL_PATTERN = re.compile(
    r"\b(?:college\s*)?(?:student\s*)?id(?:\s*number|\s*no\.?)?"
    r"\s*[:#-]\s*([A-Z0-9/-]{3,30})",
    re.IGNORECASE,
)

NAME_LABEL_PATTERN = re.compile(
    r"\bname\s*[:#-]\s*([A-Z][A-Z .'-]{1,118})",
    re.IGNORECASE,
)

COLLEGE_LABEL_PATTERN = re.compile(
    r"^.*\bcollege\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_identity_fields(ocr_text: str) -> dict:
    """
    Extract candidate identity fields from untrusted OCR text.

    These values must never determine a user's role by themselves.
    """
    if not isinstance(ocr_text, str) or not ocr_text.strip():
        return {
            "college_id_number": None,
            "name": None,
            "college_name": None,
        }

    id_match = ID_LABEL_PATTERN.search(ocr_text)
    name_match = NAME_LABEL_PATTERN.search(ocr_text)
    college_match = COLLEGE_LABEL_PATTERN.search(ocr_text)

    college_id = id_match.group(1).strip().upper() if id_match else None
    name = " ".join(name_match.group(1).split()) if name_match else None
    college_name = (
        " ".join(college_match.group(0).split())
        if college_match
        else None
    )

    return {
        "college_id_number": college_id,
        "name": name,
        "college_name": college_name,
    }
