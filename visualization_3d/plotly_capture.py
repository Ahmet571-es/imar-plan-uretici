"""
Plotly 3D Canvas Yakalama — Güvenilir sunucu tarafı export.

Kaleido ile fig.to_image() kullanarak Plotly chart'ı PNG'ye dönüştürür.
Tarayıcı tarafı JS yakalama güvenilir olmadığı için (Streamlit iframe sandbox)
sunucu tarafı yöntem birincil yöntemdir.
"""

import logging

logger = logging.getLogger(__name__)

# Kaleido mevcut mu?
_KALEIDO_AVAILABLE: bool | None = None


def is_kaleido_available() -> bool:
    """Kaleido paketinin kurulu ve çalışır durumda olduğunu kontrol eder.

    Returns:
        True ise Kaleido mevcut.
    """
    global _KALEIDO_AVAILABLE
    if _KALEIDO_AVAILABLE is not None:
        return _KALEIDO_AVAILABLE

    try:
        import kaleido  # noqa: F401
        _KALEIDO_AVAILABLE = True
    except ImportError:
        _KALEIDO_AVAILABLE = False
        logger.warning("Kaleido paketi bulunamadı. 'pip install kaleido' ile kurun.")

    return _KALEIDO_AVAILABLE


def capture_plotly_to_bytes(
    fig,
    width: int = 1536,
    height: int = 1024,
    scale: int = 2,
) -> bytes:
    """Plotly figure'ı sunucu tarafında PNG byte'larına dönüştürür.

    Kaleido ile fig.to_image() kullanır. Kaleido yoksa boş döner
    ve açık hata mesajı loglar.

    Args:
        fig: Plotly Figure nesnesi.
        width: Görsel genişliği (piksel).
        height: Görsel yüksekliği (piksel).
        scale: Ölçek çarpanı (2 = 2x çözünürlük).

    Returns:
        PNG formatında görsel byte'ları. Hata durumunda boş bytes.
    """
    if not is_kaleido_available():
        logger.error("Kaleido paketi kurulu değil. Plotly görüntü yakalama yapılamaz.")
        return b""

    try:
        img_bytes = fig.to_image(
            format="png",
            width=width,
            height=height,
            scale=scale,
        )
        logger.info(f"Plotly görüntü yakalandı: {width}x{height} scale={scale}, "
                    f"{len(img_bytes) // 1024}KB")
        return img_bytes
    except Exception as e:
        logger.error(f"Plotly görüntü yakalama hatası: {e}")
        return b""


def capture_plotly_to_base64(
    fig,
    width: int = 1536,
    height: int = 1024,
    scale: int = 2,
) -> str:
    """Plotly figure'ı base64 PNG string'e dönüştürür.

    Args:
        fig: Plotly Figure nesnesi.
        width: Görsel genişliği.
        height: Görsel yüksekliği.
        scale: Ölçek çarpanı.

    Returns:
        Base64 encoded PNG string. Hata durumunda boş string.
    """
    img_bytes = capture_plotly_to_bytes(fig, width, height, scale)
    if not img_bytes:
        return ""

    from utils.image_utils import image_bytes_to_base64
    return image_bytes_to_base64(img_bytes)
