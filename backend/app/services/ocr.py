
import os
from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError


# Use the configured executable path, with a Windows fallback.
_DEFAULT_TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = os.getenv(
    "TESSERACT_CMD",
    _DEFAULT_TESSERACT_PATH,
)


def extract_text_from_image(image_path: str | Path) -> str:
    """
    Extract text from an image using locally installed Tesseract.

    The caller is responsible for validating the upload and
    deleting any temporary image file after processing.

    Returns extracted text in memory; it does not save it.
    """
    path = Path(image_path)

    if not path.is_file():
        raise ValueError("Image file is unavailable.")

    try:
        with Image.open(path) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("Unsupported image format.")

            image.load()

            # OCR runs locally. Do not log or persist this text.
            extracted_text = pytesseract.image_to_string(
                image,
                lang="eng",
                config="--psm 6",
                timeout=15,
            )

    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or configured correctly."
        ) from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError("OCR processing failed.") from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Invalid image file.") from exc

    return extracted_text.strip()
