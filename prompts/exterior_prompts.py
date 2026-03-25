"""
Dış cephe render prompt şablonları — Grok Imagine 1.0.
Bina parametrelerinden dinamik prompt oluşturur.
"""

from prompts.style_configs import STYLE_VARIANTS, BALCONY_PROMPTS

EXTERIOR_PROMPT_TEMPLATE = """\
Photorealistic architectural exterior visualization of a {kat_sayisi}-story \
residential apartment building.

BUILDING SPECIFICATIONS:
- Footprint: {taban_en:.1f}m x {taban_boy:.1f}m
- Total height: {toplam_yukseklik:.1f}m (floor height: {kat_yuksekligi:.1f}m)
- Number of apartments per floor: {daire_sayisi_per_kat}
- Apartment type: {daire_tipi} ({daire_alan:.0f}m² each)
- Balconies: {balkon_bilgisi}

ARCHITECTURAL STYLE: {mimari_stil}
FACADE MATERIALS: {cephe_malzemesi}
CONTEXT: Urban residential neighborhood in {sehir}, Turkey
{zemin_kat_bilgisi}

CAMERA: {kamera_acisi}
LIGHTING: {aydinlatma}
QUALITY: Ultra-high resolution architectural visualization, \
professional rendering quality comparable to V-Ray or Lumion output, \
sharp details, realistic materials and textures, accurate proportions"""


def build_exterior_prompt(
    kat_sayisi: int = 4,
    taban_en: float = 20.0,
    taban_boy: float = 15.0,
    kat_yuksekligi: float = 3.0,
    daire_sayisi_per_kat: int = 2,
    daire_tipi: str = "3+1",
    daire_alan: float = 120.0,
    balkon_tipi: str = "cam_korkuluk",
    mimari_stil_key: str = "modern_minimalist",
    sehir: str = "İstanbul",
    kamera_acisi: str = "Elevated 30° corner perspective",
    aydinlatma: str = "Golden hour warm sunset",
    zemin_kat_ticari: bool = False,
) -> str:
    """Dış cephe render promptu oluşturur.

    Args:
        kat_sayisi: Bina kat sayısı.
        taban_en: Bina taban alanı genişliği (m).
        taban_boy: Bina taban alanı derinliği (m).
        kat_yuksekligi: Kat yüksekliği (m).
        daire_sayisi_per_kat: Her kattaki daire sayısı.
        daire_tipi: Daire tipi (ör: '3+1').
        daire_alan: Daire alanı (m²).
        balkon_tipi: Balkon tipi anahtarı.
        mimari_stil_key: Stil anahtarı.
        sehir: Şehir adı.
        kamera_acisi: Kamera açısı.
        aydinlatma: Aydınlatma stili.
        zemin_kat_ticari: Zemin kat ticari alan olsun mu.

    Returns:
        Oluşturulan prompt metni.
    """
    stil = STYLE_VARIANTS.get(mimari_stil_key, STYLE_VARIANTS["modern_minimalist"])
    balkon_desc = BALCONY_PROMPTS.get(balkon_tipi, "modern balconies")
    toplam_yukseklik = kat_sayisi * kat_yuksekligi

    zemin_kat_bilgisi = ""
    if zemin_kat_ticari:
        zemin_kat_bilgisi = "GROUND FLOOR: Commercial retail space with large display windows"

    return EXTERIOR_PROMPT_TEMPLATE.format(
        kat_sayisi=kat_sayisi,
        taban_en=taban_en,
        taban_boy=taban_boy,
        toplam_yukseklik=toplam_yukseklik,
        kat_yuksekligi=kat_yuksekligi,
        daire_sayisi_per_kat=daire_sayisi_per_kat,
        daire_tipi=daire_tipi,
        daire_alan=daire_alan,
        balkon_bilgisi=balkon_desc,
        mimari_stil=stil["mimari_stil"],
        cephe_malzemesi=stil["cephe_malzemesi"],
        sehir=sehir,
        kamera_acisi=kamera_acisi,
        aydinlatma=aydinlatma,
        zemin_kat_bilgisi=zemin_kat_bilgisi,
    )
