"""
İç mekan render prompt şablonları — Grok Imagine 1.0.
Oda bilgilerinden dinamik prompt oluşturur.
"""

from prompts.style_configs import STYLE_VARIANTS

INTERIOR_PROMPT_TEMPLATE = """\
Photorealistic interior architectural visualization of a {oda_tipi} \
in a modern Turkish residential apartment.

ROOM SPECIFICATIONS:
- Dimensions: {oda_en:.1f}m x {oda_boy:.1f}m ({oda_alan:.1f}m²)
- Ceiling height: {tavan_yuksekligi:.1f}m
- Windows: {pencere_bilgisi}
- Door positions: {kapi_bilgisi}

DESIGN STYLE: {ic_mekan_stili}
COLOR PALETTE: {renk_paleti}
FURNISHING LEVEL: {mobilya_seviyesi}

CAMERA: Eye-level perspective from {kamera_pozisyonu}
LIGHTING: Natural daylight + {yapay_aydinlatma}
QUALITY: Interior design magazine quality, photorealistic materials, \
accurate room proportions, professional architectural visualization"""

ROOM_TYPE_DETAILS = {
    "salon": {
        "oda_tipi_en": "spacious living room",
        "mobilya": "fully furnished with modern sofa set, coffee table, TV unit, bookshelf, and dining area",
        "kamera_pozisyonu": "entrance doorway looking into the room",
        "yapay_aydinlatma": "recessed ceiling LED lights and floor lamp",
    },
    "yatak_odasi": {
        "oda_tipi_en": "master bedroom",
        "mobilya": "furnished with king-size bed, nightstands, built-in wardrobe, and dresser",
        "kamera_pozisyonu": "corner opposite the bed",
        "yapay_aydinlatma": "warm bedside lamps and indirect ceiling lighting",
    },
    "mutfak": {
        "oda_tipi_en": "modern kitchen",
        "mobilya": "fully equipped with L-shaped counter, upper and lower cabinets, built-in appliances, breakfast bar",
        "kamera_pozisyonu": "entrance looking along the counter",
        "yapay_aydinlatma": "under-cabinet LED strips and pendant lights",
    },
    "banyo": {
        "oda_tipi_en": "modern bathroom",
        "mobilya": "equipped with walk-in shower, wall-hung toilet, double vanity sink, large mirror",
        "kamera_pozisyonu": "entrance doorway",
        "yapay_aydinlatma": "mirror backlight and recessed ceiling spots",
    },
    "antre": {
        "oda_tipi_en": "entrance hall",
        "mobilya": "with shoe cabinet, full-length mirror, coat hooks, console table",
        "kamera_pozisyonu": "front door looking inward",
        "yapay_aydinlatma": "pendant light and wall sconces",
    },
    "balkon": {
        "oda_tipi_en": "covered balcony with city view",
        "mobilya": "with outdoor lounge chair, small table, potted plants, and railing planters",
        "kamera_pozisyonu": "interior looking outward toward the view",
        "yapay_aydinlatma": "string lights and wall-mounted lantern",
    },
    "cocuk_odasi": {
        "oda_tipi_en": "children's bedroom",
        "mobilya": "with single bed, study desk, bookshelf, toy storage, and colorful decor",
        "kamera_pozisyonu": "corner opposite the bed",
        "yapay_aydinlatma": "playful pendant light and desk lamp",
    },
}

DIRECTION_MAP = {
    "south": "south-facing with abundant sunlight",
    "north": "north-facing with soft diffused light",
    "east": "east-facing with morning sunlight",
    "west": "west-facing with afternoon warm light",
    "güney": "south-facing with abundant sunlight",
    "kuzey": "north-facing with soft diffused light",
    "doğu": "east-facing with morning sunlight",
    "batı": "west-facing with afternoon warm light",
}


def build_interior_prompt(
    oda_tipi: str = "salon",
    oda_en: float = 5.0,
    oda_boy: float = 4.0,
    tavan_yuksekligi: float = 2.8,
    pencere_yonu: str = "south",
    mimari_stil_key: str = "modern_minimalist",
) -> str:
    """İç mekan render promptu oluşturur.

    Args:
        oda_tipi: Oda tipi anahtarı (salon, yatak_odasi, vb.).
        oda_en: Oda genişliği (m).
        oda_boy: Oda derinliği (m).
        tavan_yuksekligi: Tavan yüksekliği (m).
        pencere_yonu: Pencere yönü.
        mimari_stil_key: Stil anahtarı.

    Returns:
        Oluşturulan prompt metni.
    """
    stil = STYLE_VARIANTS.get(mimari_stil_key, STYLE_VARIANTS["modern_minimalist"])
    room_detail = ROOM_TYPE_DETAILS.get(oda_tipi, ROOM_TYPE_DETAILS["salon"])
    pencere_bilgisi = DIRECTION_MAP.get(pencere_yonu, "well-lit windows")
    oda_alan = oda_en * oda_boy

    return INTERIOR_PROMPT_TEMPLATE.format(
        oda_tipi=room_detail["oda_tipi_en"],
        oda_en=oda_en,
        oda_boy=oda_boy,
        oda_alan=oda_alan,
        tavan_yuksekligi=tavan_yuksekligi,
        pencere_bilgisi=pencere_bilgisi,
        kapi_bilgisi="standard door placement",
        ic_mekan_stili=stil["ic_mekan_stili"],
        renk_paleti=stil["renk_paleti"],
        mobilya_seviyesi=room_detail["mobilya"],
        kamera_pozisyonu=room_detail["kamera_pozisyonu"],
        yapay_aydinlatma=room_detail["yapay_aydinlatma"],
    )
