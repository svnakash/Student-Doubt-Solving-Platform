
from io import BytesIO
from pathlib import Path

from PIL import Image
from werkzeug.datastructures import FileStorage

from app.services.temporary_upload import temporary_image_copy


def make_jpeg():
    buffer = BytesIO()
    Image.new("RGB", (800, 400), color="white").save(
        buffer, format="JPEG"
    )
    buffer.seek(0)

    return FileStorage(
        stream=buffer,
        filename="college_id.jpg",
        content_type="image/jpeg",
    )


def test_temporary_image_exists_during_processing():
    with temporary_image_copy(make_jpeg()) as temporary_path:
        assert temporary_path.exists()
        assert temporary_path.is_file()

        with Image.open(temporary_path) as image:
            assert image.format == "JPEG"


def test_temporary_image_is_deleted_after_processing():
    saved_path = None

    with temporary_image_copy(make_jpeg()) as temporary_path:
        saved_path = temporary_path
        assert saved_path.exists()

    assert not saved_path.exists()


def test_temporary_image_is_deleted_after_exception():
    saved_path = None

    try:
        with temporary_image_copy(make_jpeg()) as temporary_path:
            saved_path = temporary_path
            assert saved_path.exists()
            raise RuntimeError("Simulated OCR failure")
    except RuntimeError:
        pass

    assert saved_path is not None
    assert not saved_path.exists()


def test_invalid_image_does_not_leave_temporary_file():
    invalid_file = FileStorage(
        stream=BytesIO(b"not an image"),
        filename="fake.jpg",
        content_type="image/jpeg",
    )

    try:
        with temporary_image_copy(invalid_file):
            raise AssertionError("Invalid image should not be processed")
    except ValueError as exc:
        assert str(exc) == "Invalid image content."
