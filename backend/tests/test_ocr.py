
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from app.services.ocr import extract_text_from_image


def test_extracts_text_from_valid_image(tmp_path):
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (800, 400), color="white").save(
        image_path, format="PNG"
    )

    with patch(
        "app.services.ocr.pytesseract.image_to_string",
        return_value="College Name\nStudent ID: TEST001",
    ) as mock_ocr:
        result = extract_text_from_image(image_path)

    assert result == "College Name\nStudent ID: TEST001"
    mock_ocr.assert_called_once()


def test_missing_image_is_rejected(tmp_path):
    missing_path = tmp_path / "missing.png"

    with pytest.raises(ValueError, match="unavailable"):
        extract_text_from_image(missing_path)


def test_unsupported_image_format_is_rejected(tmp_path):
    image_path = tmp_path / "sample.webp"
    Image.new("RGB", (800, 400), color="white").save(
        image_path, format="WEBP"
    )

    with pytest.raises(ValueError, match="Unsupported"):
        extract_text_from_image(image_path)


def test_ocr_failure_returns_controlled_error(tmp_path):
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (800, 400), color="white").save(
        image_path, format="PNG"
    )

    with patch(
        "app.services.ocr.pytesseract.image_to_string",
        side_effect=RuntimeError("simulated failure"),
    ):
        with pytest.raises(RuntimeError, match="simulated failure"):
            extract_text_from_image(image_path)
