"""
Görsel yardımcı fonksiyonları — indirme, cache, resize, base64 dönüşüm.
Grok Imagine tarafından üretilen görsellerin yönetimi.
"""

import io
import base64
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# API'ye gönderilebilecek maksimum base64 boyutu (~4MB binary = ~5.3MB base64)
MAX_BASE64_SIZE = 5_500_000
# API'ye gönderilecek görsel boyutu
API_IMAGE_MAX_WIDTH = 1536
API_IMAGE_MAX_HEIGHT = 1024


def image_bytes_to_base64(image_data: bytes) -> str:
    """Binary görsel verisini URL-safe base64 string'e dönüştürür.

    Newline ve whitespace içermeyen temiz base64 döndürür.
    Data URL formatında kullanıma uygundur.

    Args:
        image_data: Görsel binary verisi.

    Returns:
        Temiz base64 encoded string (newline yok).
    """
    if not image_data:
        return ""
    # b64encode zaten newline eklemez (encodebytes ekler), ama garanti olsun
    return base64.b64encode(image_data).decode("ascii")


def base64_to_image_bytes(b64_string: str) -> bytes:
    """Base64 string'i binary görsel verisine dönüştürür.

    Olası whitespace/newline temizliği yapar.

    Args:
        b64_string: Base64 encoded string.

    Returns:
        Binary görsel verisi.
    """
    if not b64_string:
        return b""
    # Olası whitespace temizle
    cleaned = b64_string.strip().replace("\n", "").replace("\r", "").replace(" ", "")
    try:
        return base64.b64decode(cleaned, validate=True)
    except Exception:
        # validate=True başarısız olursa, gevşek mod dene
        try:
            return base64.b64decode(cleaned)
        except Exception as e:
            logger.warning(f"Base64 decode hatası: {e}")
            return b""


def prepare_image_for_api(image_data: bytes) -> bytes:
    """Görseli API'ye gönderilmeye hazırlar: boyut küçültme + JPEG sıkıştırma.

    Büyük PNG'leri JPEG'e dönüştürür, boyutu API limitinin altına düşürür.

    Args:
        image_data: Orijinal görsel binary verisi.

    Returns:
        API'ye gönderilmeye hazır sıkıştırılmış görsel verisi.
    """
    if not image_data:
        return b""

    try:
        img = Image.open(io.BytesIO(image_data))

        # RGBA ise RGB'ye dönüştür (JPEG için gerekli)
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Boyut küçült
        img.thumbnail((API_IMAGE_MAX_WIDTH, API_IMAGE_MAX_HEIGHT), Image.LANCZOS)

        # JPEG olarak sıkıştır — kaliteyi ayarla boyut limitini tutturana kadar
        for quality in [90, 80, 70, 60]:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            result = buffer.getvalue()
            b64_size = len(base64.b64encode(result))
            if b64_size <= MAX_BASE64_SIZE:
                logger.info(f"Görsel hazırlandı: {img.size}, JPEG q={quality}, "
                           f"{len(result) // 1024}KB, base64={b64_size // 1024}KB")
                return result

        # Hala büyükse daha küçük boyut
        img.thumbnail((1024, 768), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=60, optimize=True)
        return buffer.getvalue()

    except Exception as e:
        logger.warning(f"Görsel hazırlama hatası: {e}")
        return image_data


def validate_base64_image(b64_string: str) -> tuple[bool, str]:
    """Base64 string'in geçerli bir görsel olduğunu doğrular.

    Args:
        b64_string: Doğrulanacak base64 string.

    Returns:
        (geçerli_mi, hata_mesajı) tuple'ı.
    """
    if not b64_string:
        return False, "Base64 string boş"

    if len(b64_string) > MAX_BASE64_SIZE:
        return False, f"Base64 boyutu çok büyük: {len(b64_string) // 1024}KB (max {MAX_BASE64_SIZE // 1024}KB)"

    try:
        img_bytes = base64.b64decode(b64_string, validate=True)
    except Exception as e:
        return False, f"Geçersiz base64 formatı: {e}"

    try:
        img = Image.open(io.BytesIO(img_bytes))
        img.verify()
    except Exception as e:
        return False, f"Geçersiz görsel verisi: {e}"

    return True, ""


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
    """Görsel için kare thumbnail oluşturur."""
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
    """Görsel boyutlarını döndürür."""
    if not image_data:
        return (0, 0)
    try:
        img = Image.open(io.BytesIO(image_data))
        return img.size
    except Exception:
        return (0, 0)


def render_history_to_gallery_data(render_history: list[dict]) -> list[dict]:
    """Render geçmişini galeri görünümü için düzenler."""
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
