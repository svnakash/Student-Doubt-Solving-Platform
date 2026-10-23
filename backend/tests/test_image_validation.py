
from io import BytesIO

from PIL import Image
from werkzeug.datastructures import FileStorage

from app.services.image_validation import validate_id_card_image


def make_image_file(image_format="JPEG", size=(800, 400)):
    image = Image.new("RGB", size, color="white")
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    buffer.seek(0)

    return FileStorage(
        stream=buffer,
        filename="college_id.jpg",
        content_type="image/jpeg",
    )


def test_valid_jpeg_is_accepted():
    valid, error = validate_id_card_image(make_image_file("JPEG"))

    assert valid is True
    assert error is None


def test_valid_png_is_accepted():
    valid, error = validate_id_card_image(make_image_file("PNG"))

    assert valid is True
    assert error is None


def test_missing_file_is_rejected():
    valid, error = validate_id_card_image(None)

    assert valid is False
    assert error == "IMAGE_REQUIRED"


def test_empty_file_is_rejected():
    empty_file = FileStorage(
        stream=BytesIO(b""),
        filename="empty.jpg",
        content_type="image/jpeg",
    )

    valid, error = validate_id_card_image(empty_file)

    assert valid is False
    assert error == "EMPTY_IMAGE"


def test_invalid_image_content_is_rejected():
    invalid_file = FileStorage(
        stream=BytesIO(b"This is not an image"),
        filename="fake.jpg",
        content_type="image/jpeg",
    )

    valid, error = validate_id_card_image(invalid_file)

    assert valid is False
    assert error == "INVALID_IMAGE"


def test_unsupported_image_format_is_rejected():
    valid, error = validate_id_card_image(make_image_file("WEBP"))

    assert valid is False
    assert error == "UNSUPPORTED_IMAGE_FORMAT"


def test_too_small_image_is_rejected():
    valid, error = validate_id_card_image(
        make_image_file("JPEG", size=(100, 50))
    )

    assert valid is False
    assert error == "INVALID_IMAGE_DIMENSIONS"
