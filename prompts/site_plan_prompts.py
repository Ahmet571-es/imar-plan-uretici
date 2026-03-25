"""
Site planı (arazi ve çevre konteksti) prompt şablonları — Grok Imagine 1.0.
Parsel geometrisinden kuşbakışı görsel üretir.
"""

from prompts.style_configs import PEYZAJ_PROMPTS

SITE_PLAN_PROMPT_TEMPLATE = """\
Professional aerial architectural site plan visualization.

PARCEL DATA:
- Plot dimensions: {parsel_en:.1f}m x {parsel_boy:.1f}m ({parsel_alan:.0f}m²)
- Plot shape: {parsel_sekli}

BUILDING PLACEMENT:
- Building footprint: {taban_en:.1f}m x {taban_boy:.1f}m
- Front setback (ön bahçe): {on_bahce:.1f}m
- Side setbacks (yan bahçe): {yan_bahce:.1f}m
- Rear setback (arka bahçe): {arka_bahce:.1f}m
- Building height: {bina_yuksekligi:.1f}m ({kat_sayisi} floors)

SITE ELEMENTS:
- Parking: {otopark_bilgisi}
- Landscaping: {peyzaj_bilgisi}
- Access: {giris_bilgisi}

STYLE: Professional architectural site plan, bird's eye 45-degree angle, \
clear building-to-plot relationship, accurate setback visualization, \
neighboring context indicated, north arrow, scale reference"""


def build_site_plan_prompt(
    parsel_en: float = 30.0,
    parsel_boy: float = 40.0,
    taban_en: float = 20.0,
    taban_boy: float = 15.0,
    on_bahce: float = 5.0,
    yan_bahce: float = 3.0,
    arka_bahce: float = 3.0,
    kat_sayisi: int = 4,
    kat_yuksekligi: float = 3.0,
    otopark: str = "acik",
    peyzaj_secimler: list[str] | None = None,
) -> str:
    """Site planı render promptu oluşturur.

    Args:
        parsel_en: Parsel genişliği (m).
        parsel_boy: Parsel derinliği (m).
        taban_en: Bina taban genişliği (m).
        taban_boy: Bina taban derinliği (m).
        on_bahce: Ön bahçe çekme mesafesi (m).
        yan_bahce: Yan bahçe çekme mesafesi (m).
        arka_bahce: Arka bahçe çekme mesafesi (m).
        kat_sayisi: Kat sayısı.
        kat_yuksekligi: Kat yüksekliği (m).
        otopark: Otopark tipi.
        peyzaj_secimler: Peyzaj öğeleri listesi.

    Returns:
        Oluşturulan prompt metni.
    """
    parsel_alan = parsel_en * parsel_boy
    bina_yuksekligi = kat_sayisi * kat_yuksekligi

    otopark_map = {
        "acik": "open-air surface parking with marked spaces",
        "kapali": "covered parking structure adjacent to the building",
        "bodrum": "underground basement parking garage",
    }
    otopark_bilgisi = otopark_map.get(otopark, otopark_map["acik"])

    if peyzaj_secimler:
        peyzaj_parts = [PEYZAJ_PROMPTS.get(p, p) for p in peyzaj_secimler]
        peyzaj_bilgisi = ", ".join(peyzaj_parts)
    else:
        peyzaj_bilgisi = "basic landscaping with lawn and pathways"

    # Parsel şekli tahmin
    oran = parsel_en / parsel_boy if parsel_boy > 0 else 1
    if 0.85 <= oran <= 1.15:
        parsel_sekli = "approximately square"
    elif oran < 0.85:
        parsel_sekli = "rectangular (deeper than wide)"
    else:
        parsel_sekli = "rectangular (wider than deep)"

    return SITE_PLAN_PROMPT_TEMPLATE.format(
        parsel_en=parsel_en,
        parsel_boy=parsel_boy,
        parsel_alan=parsel_alan,
        parsel_sekli=parsel_sekli,
        taban_en=taban_en,
        taban_boy=taban_boy,
        on_bahce=on_bahce,
        yan_bahce=yan_bahce,
        arka_bahce=arka_bahce,
        bina_yuksekligi=bina_yuksekligi,
        kat_sayisi=kat_sayisi,
        otopark_bilgisi=otopark_bilgisi,
        peyzaj_bilgisi=peyzaj_bilgisi,
        giris_bilgisi="main entrance driveway from street with pedestrian walkway",
    )
