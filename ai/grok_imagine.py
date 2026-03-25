"""
Grok Imagine 1.0 API Wrapper — xAI görsel üretim ve düzenleme.

Text-to-Image ve Image-to-Image editing endpoint'lerini yönetir.
OpenAI SDK uyumlu generation + doğrudan HTTP request ile editing.
"""

import io
import time
import logging
import base64
from dataclasses import dataclass, field
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# ── Sabitler ──
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_IMAGE_MODEL = "grok-imagine-image"
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION = "2k"
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # saniye, üstel geri çekilme


@dataclass
class ImageResult:
    """Görsel üretim/düzenleme sonucu."""

    image_url: str = ""
    image_data: bytes = b""
    prompt: str = ""
    timestamp: str = ""
    render_type: str = ""
    style: str = ""
    success: bool = False
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Session state'te saklanabilecek dict formatı."""
        return {
            "url": self.image_url,
            "image_data_b64": base64.b64encode(self.image_data).decode() if self.image_data else "",
            "prompt": self.prompt,
            "timestamp": self.timestamp,
            "render_type": self.render_type,
            "style": self.style,
            "success": self.success,
            "metadata": self.metadata,
        }


def _get_openai_client(api_key: str):
    """xAI uyumlu OpenAI client oluşturur."""
    from openai import OpenAI

    return OpenAI(base_url=XAI_BASE_URL, api_key=api_key)


def _download_image(url: str, timeout: int = 30) -> bytes:
    """URL'den görseli indirir. Geçici URL'ler için hemen çağrılmalıdır.

    Args:
        url: Görsel URL'si.
        timeout: İndirme zaman aşımı (saniye).

    Returns:
        Görsel binary verisi.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.warning(f"Görsel indirme hatası: {e}")
        return b""


def generate_image(
    prompt: str,
    api_key: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    resolution: str = DEFAULT_RESOLUTION,
    render_type: str = "exterior",
    style: str = "",
) -> ImageResult:
    """Grok Imagine ile text-to-image görsel üretir.

    Args:
        prompt: Görsel üretim promptu.
        api_key: xAI API anahtarı.
        aspect_ratio: En-boy oranı (ör: '16:9', '3:2').
        resolution: Çözünürlük ('default' veya '2k').
        render_type: Render tipi (exterior, interior, site_plan, vb.).
        style: Mimari stil adı.

    Returns:
        ImageResult nesnesi.
    """
    result = ImageResult(
        prompt=prompt,
        timestamp=datetime.now().isoformat(),
        render_type=render_type,
        style=style,
    )

    if not api_key:
        result.error = "xAI API anahtarı gerekli."
        return result

    for attempt in range(MAX_RETRIES):
        try:
            client = _get_openai_client(api_key)
            extra = {"aspect_ratio": aspect_ratio}
            if resolution and resolution != "default":
                extra["resolution"] = resolution

            response = client.images.generate(
                model=XAI_IMAGE_MODEL,
                prompt=prompt,
                extra_body=extra,
            )

            if response.data and len(response.data) > 0:
                result.image_url = response.data[0].url or ""
                result.success = True
                # Görseli hemen indir — URL'ler geçici
                if result.image_url:
                    result.image_data = _download_image(result.image_url)
                logger.info(f"Görsel üretildi: {render_type}/{style}")
                return result
            else:
                result.error = "API yanıtında görsel verisi yok"
                return result

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAY_BASE ** (attempt + 1)
                    logger.warning(f"Rate limit, {wait}s bekleniyor... (deneme {attempt + 1})")
                    time.sleep(wait)
                    continue
            result.error = f"Görsel üretim hatası: {error_msg}"
            logger.error(result.error)
            return result

    result.error = f"Maksimum deneme sayısına ({MAX_RETRIES}) ulaşıldı."
    return result


def edit_image(
    image_url: str,
    edit_prompt: str,
    api_key: str,
    image_base64: str = "",
) -> ImageResult:
    """Grok Imagine ile mevcut görseli düzenler.

    NOT: OpenAI SDK'nın images.edit() metodu xAI'da çalışmaz
    (multipart/form-data vs application/json uyumsuzluğu).
    Doğrudan HTTP request kullanır.

    Args:
        image_url: Düzenlenecek görselin URL'si.
        edit_prompt: Düzenleme talimatı.
        api_key: xAI API anahtarı.
        image_base64: Alternatif olarak base64 formatında görsel.

    Returns:
        ImageResult nesnesi.
    """
    result = ImageResult(
        prompt=f"EDIT: {edit_prompt}",
        timestamp=datetime.now().isoformat(),
        render_type="edit",
    )

    if not api_key:
        result.error = "xAI API anahtarı gerekli."
        return result

    # Kaynak görsel: URL veya base64
    if image_base64:
        image_source = {
            "url": f"data:image/png;base64,{image_base64}",
            "type": "image_url",
        }
    elif image_url:
        image_source = {
            "url": image_url,
            "type": "image_url",
        }
    else:
        result.error = "Düzenlenecek görsel URL'si veya base64 verisi gerekli."
        return result

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": XAI_IMAGE_MODEL,
        "prompt": edit_prompt,
        "image": image_source,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                f"{XAI_BASE_URL}/images/edits",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if resp.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAY_BASE ** (attempt + 1)
                    logger.warning(f"Rate limit (edit), {wait}s bekleniyor...")
                    time.sleep(wait)
                    continue

            resp.raise_for_status()
            data = resp.json()

            if "data" in data and len(data["data"]) > 0:
                result.image_url = data["data"][0].get("url", "")
                result.success = True
                if result.image_url:
                    result.image_data = _download_image(result.image_url)
                logger.info("Görsel düzenleme tamamlandı")
                return result
            else:
                result.error = f"API yanıtında görsel yok: {data}"
                return result

        except requests.exceptions.HTTPError as e:
            result.error = f"HTTP hatası: {e.response.status_code} — {e.response.text[:200]}"
            logger.error(result.error)
            return result
        except Exception as e:
            result.error = f"Düzenleme hatası: {str(e)}"
            logger.error(result.error)
            return result

    result.error = f"Maksimum deneme sayısına ({MAX_RETRIES}) ulaşıldı."
    return result


def generate_style_comparison(
    prompt_builder_func,
    prompt_kwargs: dict,
    api_key: str,
    styles: list[str] | None = None,
) -> list[ImageResult]:
    """4 farklı mimari stilde paralel görsel üretir.

    Args:
        prompt_builder_func: Prompt oluşturma fonksiyonu.
        prompt_kwargs: Prompt fonksiyonuna geçilecek parametreler.
        api_key: xAI API anahtarı.
        styles: Stil anahtarları listesi. None ise tüm stiller kullanılır.

    Returns:
        ImageResult listesi.
    """
    from prompts.style_configs import STYLE_VARIANTS

    if styles is None:
        styles = list(STYLE_VARIANTS.keys())

    results = []
    for style_key in styles:
        kwargs = dict(prompt_kwargs)
        kwargs["mimari_stil_key"] = style_key
        prompt = prompt_builder_func(**kwargs)
        result = generate_image(
            prompt=prompt,
            api_key=api_key,
            render_type="style_comparison",
            style=STYLE_VARIANTS[style_key]["isim"],
        )
        results.append(result)

    return results


def get_threejs_screenshot_js() -> str:
    """Three.js/Plotly canvas'tan ekran görüntüsü almak için JavaScript kodu.

    Returns:
        HTML/JS kodu.
    """
    return """
    <script>
    function captureCanvas() {
        // Plotly veya Three.js canvas'ını bul
        const canvases = document.querySelectorAll('canvas');
        let targetCanvas = null;

        for (const canvas of canvases) {
            if (canvas.width > 100 && canvas.height > 100) {
                targetCanvas = canvas;
                break;
            }
        }

        if (targetCanvas) {
            const dataURL = targetCanvas.toDataURL('image/png');
            // Streamlit'e gönder
            window.parent.postMessage({
                type: 'canvas_screenshot',
                data: dataURL
            }, '*');
            return dataURL;
        }
        return null;
    }
    </script>
    """
