"""
Grok Imagine 1.0 API Wrapper — xAI görsel üretim ve düzenleme.

Text-to-Image ve Image-to-Image editing endpoint'lerini yönetir.
OpenAI SDK uyumlu generation + doğrudan HTTP request ile editing.

Hata Güvenliği:
- Base64 pre-validation ve temizleme
- Görsel boyut sıkıştırma (API limitini aşmamak için)
- Retry logic (rate limit + network hataları)
- Detaylı hata mesajları
"""

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
API_TIMEOUT = 90  # saniye — render uzun sürebilir


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
        from utils.image_utils import image_bytes_to_base64
        return {
            "url": self.image_url,
            "image_data_b64": image_bytes_to_base64(self.image_data),
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
    """URL'den görseli indirir. Geçici URL'ler için hemen çağrılmalıdır."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.warning(f"Görsel indirme hatası: {e}")
        return b""


def _clean_base64(b64_string: str) -> str:
    """Base64 string'i temizler: whitespace, newline, data URL prefix kaldırır."""
    if not b64_string:
        return ""
    # data:image/...;base64, prefix'i kaldır
    if b64_string.startswith("data:"):
        parts = b64_string.split(",", 1)
        if len(parts) == 2:
            b64_string = parts[1]
    # Whitespace temizle
    return b64_string.strip().replace("\n", "").replace("\r", "").replace(" ", "")


def _is_retryable_error(error_msg: str) -> bool:
    """Yeniden denenebilir hata mı kontrol eder."""
    retryable = ["rate_limit", "429", "timeout", "connection", "503", "502"]
    lower = error_msg.lower()
    return any(r in lower for r in retryable)


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
                if result.image_url:
                    result.image_data = _download_image(result.image_url)
                logger.info(f"Görsel üretildi: {render_type}/{style}")
                return result
            else:
                result.error = "API yanıtında görsel verisi yok"
                return result

        except Exception as e:
            error_msg = str(e)
            if _is_retryable_error(error_msg) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_BASE ** (attempt + 1)
                logger.warning(f"Yeniden denenebilir hata, {wait}s bekleniyor... (deneme {attempt + 1})")
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
        cleaned_b64 = _clean_base64(image_base64)
        if not cleaned_b64:
            result.error = "Base64 görsel verisi boş veya geçersiz."
            return result

        # Pre-validation: base64 boyut kontrolü
        from utils.image_utils import validate_base64_image, prepare_image_for_api
        valid, err_msg = validate_base64_image(cleaned_b64)
        if not valid:
            # Boyut sorunu ise sıkıştır
            if "büyük" in err_msg or "boyut" in err_msg.lower():
                logger.info("Base64 çok büyük, sıkıştırılıyor...")
                try:
                    raw_bytes = base64.b64decode(cleaned_b64)
                    compressed = prepare_image_for_api(raw_bytes)
                    cleaned_b64 = base64.b64encode(compressed).decode("ascii")
                    valid, err_msg = validate_base64_image(cleaned_b64)
                except Exception as e:
                    result.error = f"Görsel sıkıştırma hatası: {e}"
                    return result

            if not valid:
                result.error = f"Görsel doğrulama hatası: {err_msg}"
                return result

        image_source = {
            "url": f"data:image/jpeg;base64,{cleaned_b64}",
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
                timeout=API_TIMEOUT,
            )

            if resp.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAY_BASE ** (attempt + 1)
                    logger.warning(f"Rate limit (edit), {wait}s bekleniyor...")
                    time.sleep(wait)
                    continue

            if resp.status_code == 413:
                result.error = "Görsel boyutu çok büyük (413 Payload Too Large). Daha küçük görsel deneyin."
                return result

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
            status = e.response.status_code if e.response is not None else "?"
            body = e.response.text[:500] if e.response is not None else "Yanıt yok"
            result.error = f"HTTP hatası {status}: {body}"
            logger.error(result.error)

            if _is_retryable_error(str(status)) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_BASE ** (attempt + 1)
                time.sleep(wait)
                continue
            return result

        except requests.exceptions.Timeout:
            result.error = f"API zaman aşımı ({API_TIMEOUT}s). Sunucu yoğun olabilir."
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_BASE ** (attempt + 1))
                continue
            return result

        except Exception as e:
            result.error = f"Düzenleme hatası: {str(e)}"
            logger.error(result.error)
            return result

    result.error = f"Maksimum deneme sayısına ({MAX_RETRIES}) ulaşıldı."
    return result


def render_3d_to_photorealistic(
    captured_image_bytes: bytes,
    api_key: str,
    kat_sayisi: int = 4,
    taban_en: float = 20.0,
    taban_boy: float = 15.0,
    mimari_stil_key: str = "modern_minimalist",
    aydinlatma: str = "Golden hour warm sunset",
    ek_prompt: str = "",
) -> ImageResult:
    """3D wireframe görüntüsünü fotorealistik render'a dönüştürür.

    Strateji: Önce text-to-image ile bina parametrelerinden fotorealistik render üret.
    Wireframe'i doğrudan edit endpoint'e göndermek güvenilir değil çünkü
    edit endpoint fotoğraf düzenleme için tasarlanmış, wireframe dönüşümü için değil.

    Args:
        captured_image_bytes: Yakalanan 3D görüntünün binary verisi.
        api_key: xAI API anahtarı.
        kat_sayisi: Bina kat sayısı.
        taban_en: Bina taban genişliği (m).
        taban_boy: Bina taban derinliği (m).
        mimari_stil_key: Mimari stil anahtarı.
        aydinlatma: Aydınlatma açıklaması.
        ek_prompt: Kullanıcının ek talimatı.

    Returns:
        ImageResult nesnesi.
    """
    from prompts.exterior_prompts import build_exterior_prompt
    from utils.image_utils import prepare_image_for_api, image_bytes_to_base64

    # ── Adım 1: Text-to-image ile fotorealistik temel render üret ──
    prompt = build_exterior_prompt(
        kat_sayisi=kat_sayisi,
        taban_en=taban_en,
        taban_boy=taban_boy,
        mimari_stil_key=mimari_stil_key,
        aydinlatma=aydinlatma,
    )
    if ek_prompt:
        prompt += f"\nAdditional requirements: {ek_prompt}"

    logger.info("Adım 1: Text-to-image fotorealistik render üretiliyor...")
    base_result = generate_image(
        prompt=prompt,
        api_key=api_key,
        render_type="3d_to_photorealistic",
        style=mimari_stil_key,
    )

    if not base_result.success:
        return base_result

    # ── Adım 2: Eğer yakalanmış görüntü varsa, composition hint olarak edit dene ──
    if captured_image_bytes and base_result.image_url:
        logger.info("Adım 2: Yakalanan 3D açıya uygun düzenleme deneniyor...")
        compressed = prepare_image_for_api(captured_image_bytes)
        compressed_b64 = image_bytes_to_base64(compressed)

        if compressed_b64:
            # Edit ile 3D modelin açısına yaklaştırmayı dene
            edit_prompt = (
                f"Adjust this photorealistic building render to match the viewing angle "
                f"and composition of the reference 3D model. Maintain the photorealistic quality, "
                f"{aydinlatma} lighting, and architectural style. "
                f"Keep all realistic materials and textures intact."
            )
            if ek_prompt:
                edit_prompt += f" {ek_prompt}"

            edit_result = edit_image(
                image_url=base_result.image_url,
                edit_prompt=edit_prompt,
                api_key=api_key,
            )

            if edit_result.success:
                edit_result.render_type = "3d_to_photorealistic"
                edit_result.style = base_result.style
                edit_result.metadata["method"] = "text-to-image + edit refinement"
                logger.info("Adım 2 başarılı: Edit ile iyileştirme tamamlandı")
                return edit_result
            else:
                # Edit başarısız — adım 1 sonucu zaten iyi, onu döndür
                logger.info(f"Adım 2 atlandı (edit hatası: {edit_result.error}), "
                           "adım 1 sonucu kullanılıyor.")

    base_result.metadata["method"] = "text-to-image (direct)"
    return base_result


def generate_style_comparison(
    prompt_builder_func,
    prompt_kwargs: dict,
    api_key: str,
    styles: list[str] | None = None,
) -> list[ImageResult]:
    """4 farklı mimari stilde görsel üretir.

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
