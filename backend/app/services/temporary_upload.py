
import tempfile
from contextlib import contextmanager
from pathlib import Path

from PIL import Image, UnidentifiedImageError


@contextmanager
def temporary_image_copy(file_storage):
    """
    Save an upload to a temporary file for processing.

    The temporary file is removed when the context exits,
    including when processing raises an exception.
    """
    temporary_path = None

    try:
        suffix = Path(file_storage.filename or "").suffix.lower()

        # Do not trust the original filename or use it as a path.
        if suffix not in {".jpg", ".jpeg", ".png"}:
            suffix = ".img"

        with tempfile.NamedTemporaryFile(
            prefix="student_id_",
            suffix=suffix,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            file_storage.stream.seek(0)

            while True:
                chunk = file_storage.stream.read(64 * 1024)

                if not chunk:
                    break

                temporary_file.write(chunk)

        # Reopen and decode the temporary copy before processing.
        with Image.open(temporary_path) as image:
            image.verify()

        with Image.open(temporary_path) as image:
            image.load()

        yield temporary_path

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise ValueError("Invalid image content.") from exc

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
