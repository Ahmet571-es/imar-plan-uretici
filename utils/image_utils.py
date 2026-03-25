"""
Görsel yardımcı fonksiyonları — indirme, cache, resize, base64 dönüşüm.
Grok Imagine tarafından üretilen görsellerin yönetimi.
"""

import io
import base64
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def image_bytes_to_base64(image_data: bytes) -> str:
    """Binary görsel verisini base64 string'e dönüştürür.

    Args:
        image_data: Görsel binary verisi.

    Returns:
        Base64 encoded string.
    """
    if not image_data:
        return ""
    return base64.b64encode(image_data).decode("utf-8")


def base64_to_image_bytes(b64_string: str) -> bytes:
    """Base64 string'i binary görsel verisine dönüştürür.

    Args:
        b64_string: Base64 encoded string.

    Returns:
        Binary görsel verisi.
    """
    if not b64_string:
        return b""
    return base64.b64decode(b64_string)


def resize_image(
    image_data: bytes,
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 90,
) -> bytes:
    """Görseli belirtilen boyutlara sığdırır (aspect ratio koruyarak).

    Args:
        image_data: Görsel binary verisi.
        max_width: Maksimum genişlik.
        max_height: Maksimum yükseklik.
        quality: JPEG kalitesi (1-100).

    Returns:
        Yeniden boyutlandırılmış görsel verisi.
    """
    if not image_data:
        return b""

    try:
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail((max_width, max_height), Image.LANCZOS)

        buffer = io.BytesIO()
        fmt = img.format or "PNG"
        if fmt == "JPEG":
            img.save(buffer, format=fmt, quality=quality)
        else:
            img.save(buffer, format=fmt)
        return buffer.getvalue()
    except Exception as e:
        logger.warning(f"Görsel yeniden boyutlandırma hatası: {e}")
        return image_data


def create_thumbnail(image_data: bytes, size: int = 300) -> bytes:
    """Görsel için kare thumbnail oluşturur.

    Args:
        image_data: Görsel binary verisi.
        size: Thumbnail boyutu (piksel).

    Returns:
        Thumbnail görsel verisi.
    """
    if not image_data:
        return b""

    try:
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail((size, size), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception as e:
        logger.warning(f"Thumbnail oluşturma hatası: {e}")
        return b""


def get_image_dimensions(image_data: bytes) -> tuple[int, int]:
    """Görsel boyutlarını döndürür.

    Args:
        image_data: Görsel binary verisi.

    Returns:
        (genişlik, yükseklik) tuple'ı.
    """
    if not image_data:
        return (0, 0)

    try:
        img = Image.open(io.BytesIO(image_data))
        return img.size
    except Exception:
        return (0, 0)


def render_history_to_gallery_data(render_history: list[dict]) -> list[dict]:
    """Render geçmişini galeri görünümü için düzenler.

    Args:
        render_history: Session state'teki render geçmişi listesi.

    Returns:
        Galeri formatında düzenlenmiş liste.
    """
    gallery = []
    for i, item in enumerate(render_history):
        entry = {
            "index": i,
            "has_image": bool(item.get("image_data_b64")),
            "prompt": item.get("prompt", ""),
            "timestamp": item.get("timestamp", ""),
            "render_type": item.get("render_type", ""),
            "style": item.get("style", ""),
        }
        gallery.append(entry)
    return gallery
