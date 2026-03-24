"""
Fotogerçekçi İç Mekan Render — Grok Imagine API (xAI) entegrasyonu.
Oda bilgilerinden otomatik prompt oluşturur ve AI ile render üretir.
"""

import os
import logging
import base64
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

RENDER_STYLES = {
    "modern_turk": {
        "isim": "Modern Türk",
        "aciklama": "Sade, beyaz-gri tonlar, ahşap detaylar",
        "prompt_suffix": "modern Turkish style, clean lines, white and gray tones, warm wood accents, natural materials",
    },
    "klasik_turk": {
        "isim": "Klasik Türk",
        "aciklama": "Sıcak tonlar, geleneksel motifler",
        "prompt_suffix": "classic Turkish style, warm earth tones, traditional patterns, ornate details, rich textures",
    },
    "minimalist": {
        "isim": "Minimalist",
        "aciklama": "Siyah-beyaz, clean lines",
        "prompt_suffix": "minimalist style, monochromatic, clean geometric lines, open space, natural light",
    },
    "luks": {
        "isim": "Lüks",
        "aciklama": "Mermer, kristal, gold detaylar",
        "prompt_suffix": "luxury style, marble floors, crystal chandelier, gold accents, premium materials, high-end furniture",
    },
}

ROOM_TYPE_DESCRIPTIONS = {
    "salon": "living room with sofa set, coffee table, TV unit, and dining area",
    "yatak_odasi": "bedroom with double bed, nightstands, wardrobe, and soft lighting",
    "mutfak": "kitchen with modern cabinets, countertop, appliances, and good lighting",
    "banyo": "bathroom with shower cabin, modern sink, and clean tiles",
    "antre": "entrance hall with shoe cabinet, mirror, and coat hanger",
    "balkon": "balcony with outdoor furniture and plants",
}


@dataclass
class RenderResult:
    """Render sonucu."""
    image_url: str = ""
    image_data: bytes = b""
    prompt: str = ""
    style: str = ""
    room_name: str = ""
    success: bool = False
    error: str = ""


def generate_render(
    room_name: str,
    room_type: str,
    room_area: float,
    window_direction: str = "south",
    style: str = "modern_turk",
    api_key: str = "",
) -> RenderResult:
    """Bir oda için fotogerçekçi render üretir.

    Args:
        room_name: Oda adı (ör: "Salon").
        room_type: Oda tipi (ör: "salon").
        room_area: Oda alanı (m²).
        window_direction: Pencere yönü.
        style: Render stili.
        api_key: Grok/xAI API anahtarı.

    Returns:
        RenderResult nesnesi.
    """
    result = RenderResult(room_name=room_name, style=style)

    # Prompt oluştur
    prompt = _build_render_prompt(room_name, room_type, room_area, window_direction, style)
    result.prompt = prompt

    if not api_key:
        api_key = os.getenv("XAI_API_KEY", "")

    if not api_key:
        result.error = "Grok API key bulunamadı. Render üretimi için XAI_API_KEY gerekli."
        logger.warning(result.error)
        return result

    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)

        response = client.images.generate(
            model="grok-2-image",
            prompt=prompt,
        )

        if response.data and len(response.data) > 0:
            result.image_url = response.data[0].url or ""
            result.success = True
            logger.info(f"Render oluşturuldu: {room_name}")

            # URL'den image data indir
            if result.image_url:
                try:
                    img_response = requests.get(result.image_url, timeout=30)
                    result.image_data = img_response.content
                except Exception:
                    pass
        else:
            result.error = "API yanıtında görüntü verisi yok"

    except Exception as e:
        result.error = f"Render hatası: {str(e)}"
        logger.error(result.error)

    return result


def _build_render_prompt(
    room_name: str,
    room_type: str,
    room_area: float,
    window_direction: str,
    style: str,
) -> str:
    """Render prompt'u oluşturur."""
    room_desc = ROOM_TYPE_DESCRIPTIONS.get(room_type, f"{room_type} room")
    style_info = RENDER_STYLES.get(style, RENDER_STYLES["modern_turk"])
    style_suffix = style_info["prompt_suffix"]

    direction_map = {
        "south": "south-facing", "north": "north-facing",
        "east": "east-facing", "west": "west-facing",
        "güney": "south-facing", "kuzey": "north-facing",
        "doğu": "east-facing", "batı": "west-facing",
    }
    direction_text = direction_map.get(window_direction, "well-lit")

    prompt = (
        f"Photorealistic interior architectural visualization of a {room_area:.0f} square meter "
        f"Turkish {room_desc}, {direction_text} windows with abundant natural daylight, "
        f"{style_suffix}, high quality 4K architectural rendering, "
        f"professional interior photography, realistic materials and textures, "
        f"proper scale and proportions, warm ambient lighting"
    )

    return prompt


def generate_room_gallery(
    rooms: list[dict],
    style: str = "modern_turk",
    api_key: str = "",
) -> list[RenderResult]:
    """Birden fazla oda için render galerisi üretir."""
    results = []
    for room in rooms:
        render = generate_render(
            room_name=room.get("isim", "Oda"),
            room_type=room.get("tip", "salon"),
            room_area=room.get("m2", 20),
            window_direction=room.get("yon", "south"),
            style=style,
            api_key=api_key,
        )
        results.append(render)
    return results
