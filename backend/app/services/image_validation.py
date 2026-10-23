
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_DIMENSION = 6000
MIN_IMAGE_WIDTH = 200
MIN_IMAGE_HEIGHT = 100

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}


def validate_id_card_image(file_storage):
    """
    Validate an uploaded ID-card image without saving it.

    Returns:
        (True, None) when valid.
        (False, error_code) when invalid.
    """
    if file_storage is None:
        return False, "IMAGE_REQUIRED"

    uploaded_file = file_storage.stream

    # Check actual file size, not only the declared content length.
    uploaded_file.seek(0, 2)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)

    if file_size == 0:
        return False, "EMPTY_IMAGE"

    if file_size > MAX_IMAGE_SIZE_BYTES:
        return False, "IMAGE_TOO_LARGE"

    try:
        with Image.open(uploaded_file) as image:
            image_format = image.format
            width, height = image.size

            if image_format not in ALLOWED_IMAGE_FORMATS:
                return False, "UNSUPPORTED_IMAGE_FORMAT"

            if (
                width < MIN_IMAGE_WIDTH
                or height < MIN_IMAGE_HEIGHT
                or width > MAX_IMAGE_DIMENSION
                or height > MAX_IMAGE_DIMENSION
            ):
                return False, "INVALID_IMAGE_DIMENSIONS"

            # Verify the image structure.
            image.verify()

        # verify() checks the file structure; reopen and decode it too.
        uploaded_file.seek(0)

        with Image.open(uploaded_file) as image:
            image.load()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ):
        return False, "INVALID_IMAGE"

    finally:
        uploaded_file.seek(0)

    return True, None
