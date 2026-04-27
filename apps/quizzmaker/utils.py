from django.core.exceptions import ValidationError
from PIL import Image

MAX_IMAGE_SIZE = 8 * 1024 * 1024  # 8 MB
MAX_GIF_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_GIF_FRAMES = 300
MAX_IMAGE_DIM = 2000  # px


def validate_upload(uploaded_file):
    if not uploaded_file:
        return
    name = (getattr(uploaded_file, "name", "") or "").lower()
    is_gif = (
        getattr(uploaded_file, "content_type", "") == "image/gif"
        or name.endswith(".gif")
    )
    size = getattr(uploaded_file, "size", 0) or 0
    cap = MAX_GIF_SIZE if is_gif else MAX_IMAGE_SIZE
    if size > cap:
        raise ValidationError(
            f"File too large ({size // 1024} KB). Max {cap // (1024 * 1024)} MB."
        )
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        w, h = img.size
        n_frames = getattr(img, "n_frames", 1) if is_gif else 1
    except Exception as exc:
        raise ValidationError("Invalid image file.") from exc
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
    if w > MAX_IMAGE_DIM or h > MAX_IMAGE_DIM:
        raise ValidationError(
            f"Image too large ({w}×{h}). Max {MAX_IMAGE_DIM}×{MAX_IMAGE_DIM}."
        )
    if is_gif and n_frames > MAX_GIF_FRAMES:
        raise ValidationError(
            f"GIF has {n_frames} frames. Max {MAX_GIF_FRAMES}."
        )
