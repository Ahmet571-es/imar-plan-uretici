"""
Koridor düzenleri — layout tipi seçimi ve koridor omurgası oluşturma.

Desteklenen layout tipleri:
- center_corridor: Klasik merkez koridor
- l_shape: L-şekilli koridor
- t_shape: T-şekilli koridor
- short_corridor: Kısa koridor (kompakt)
- open_plan: Açık plan düzeni
"""

import random
from core.plan_scorer import PlanRoom


# ═══════════════════════════════════════════════════════════════
# LAYOUT TİPLERİ
# ═══════════════════════════════════════════════════════════════

LAYOUT_TYPES = [
    "center_corridor",     # Merkez koridor (klasik)
    "l_shape",             # L-şekilli koridor
    "t_shape",             # T-şekilli koridor
    "short_corridor",      # Kısa koridor (kompakt)
    "open_plan",           # Salon-mutfak açık plan
]


# ═══════════════════════════════════════════════════════════════
# LAYOUT TİPİ SEÇİMİ VE KORİDOR OMURGASI
# ═══════════════════════════════════════════════════════════════

def _select_layout_type(bw: float, bh: float, apt_type: str,
                         seed: int | None) -> str:
    """Bina boyutları ve daire tipine göre layout tipi seçer."""
    aspect = bw / bh if bh > 0 else 1.0

    # Ağırlıklı olasılıklar
    weights = {
        "center_corridor": 0.25,
        "l_shape": 0.20,
        "t_shape": 0.15,
        "short_corridor": 0.20,
        "open_plan": 0.20,
    }

    # Dar parsellerde L-şekil tercih
    if aspect < 0.7:
        weights["l_shape"] = 0.35
        weights["center_corridor"] = 0.15
    # Geniş parsellerde T-şekil tercih
    elif aspect > 1.5:
        weights["t_shape"] = 0.30
        weights["center_corridor"] = 0.15
    # Küçük dairelerde kısa koridor tercih
    if apt_type in ("1+1", "2+1"):
        weights["short_corridor"] = 0.35
        weights["t_shape"] = 0.10

    layout_list = list(weights.keys())
    layout_weights = [weights[k] for k in layout_list]
    return random.choices(layout_list, weights=layout_weights, k=1)[0]


def _create_corridor_spine(bw, bh, ox, oy, entrance_side, layout_type):
    """Koridor omurgası ve yerleştirme bölgeleri — layout tipine göre.

    Tipik Türk dairesi düzeni:
    ┌──────────────────────────────┐
    │  Yatak 1  │ Koridor │ Banyo  │  ← Arka (kuzey)
    │───────────│         │────────│
    │  Yatak 2  │         │  WC    │
    │───────────│         │────────│
    │   Salon   │         │ Mutfak │  ← Ön (güney, giriş)
    │  +Balkon  │  Antre  │        │
    └──────────────────────────────┘
    """
    if layout_type == "l_shape":
        return _create_l_corridor(bw, bh, ox, oy, entrance_side)
    elif layout_type == "t_shape":
        return _create_t_corridor(bw, bh, ox, oy, entrance_side)
    elif layout_type == "short_corridor":
        return _create_short_corridor(bw, bh, ox, oy, entrance_side)
    elif layout_type == "open_plan":
        return _create_open_plan_corridor(bw, bh, ox, oy, entrance_side)
    else:
        return _create_center_corridor(bw, bh, ox, oy, entrance_side)


def _create_center_corridor(bw, bh, ox, oy, entrance_side):
    """Klasik merkez koridor düzeni."""
    corridor_w = 1.20

    # Koridor pozisyonu: varyasyon için rastgele
    corr_ratio = 0.35 + random.random() * 0.20
    corr_x = ox + bw * corr_ratio

    corridor = PlanRoom(
        name="Koridor", room_type="koridor",
        x=round(corr_x, 2), y=round(oy, 2),
        width=round(corridor_w, 2), height=round(bh, 2),
        has_exterior_wall=False,
    )

    left_w = corr_x - ox
    right_w = bw - (corr_x - ox + corridor_w)
    right_x = corr_x + corridor_w

    zones = {
        "corridor": {"x": corr_x, "y": oy, "w": corridor_w, "h": bh},
        "left_front": {"x": ox, "y": oy, "w": left_w, "h": bh * 0.50,
                       "remaining_area": left_w * bh * 0.50},
        "left_back":  {"x": ox, "y": oy + bh * 0.50, "w": left_w,
                       "h": bh * 0.50,
                       "remaining_area": left_w * bh * 0.50},
        "right_front": {"x": right_x, "y": oy, "w": right_w,
                        "h": bh * 0.30,
                        "remaining_area": right_w * bh * 0.30},
        "right_mid":   {"x": right_x, "y": oy + bh * 0.30, "w": right_w,
                        "h": bh * 0.25,
                        "remaining_area": right_w * bh * 0.25},
        "right_back":  {"x": right_x, "y": oy + bh * 0.55, "w": right_w,
                        "h": bh * 0.45,
                        "remaining_area": right_w * bh * 0.45},
        "entrance":  {"x": corr_x - 1.2, "y": oy,
                      "w": corridor_w + 1.2, "h": 2.2,
                      "remaining_area": (corridor_w + 1.2) * 2.2},
        "wet":       {"x": right_x, "y": oy + bh * 0.30, "w": right_w,
                      "h": bh * 0.70,
                      "remaining_area": right_w * bh * 0.70},
    }

    return corridor, zones


def _create_l_corridor(bw, bh, ox, oy, entrance_side):
    """L-şekilli koridor düzeni — koridorun köşede dönmesi."""
    corridor_w = 1.20

    # Dikey kol: üst yarıda
    vert_x = ox + bw * (0.35 + random.random() * 0.15)
    vert_y_start = oy + bh * 0.45
    vert_h = bh * 0.55

    # Yatay kol: ortadan sağa
    horiz_y = vert_y_start
    horiz_x_start = vert_x
    horiz_w = ox + bw - vert_x

    corridor = PlanRoom(
        name="Koridor", room_type="koridor",
        x=round(vert_x, 2), y=round(vert_y_start, 2),
        width=round(corridor_w, 2), height=round(vert_h, 2),
        has_exterior_wall=False,
    )

    # L-şekilli koridorun yatay kolu (ikinci PlanRoom olarak eklenmez,
    # zone olarak kullanılır)
    left_w = vert_x - ox
    right_x = vert_x + corridor_w
    right_w = bw - (vert_x - ox + corridor_w)

    zones = {
        "corridor": {"x": vert_x, "y": vert_y_start, "w": corridor_w,
                     "h": vert_h},
        "left_front": {"x": ox, "y": oy, "w": left_w, "h": bh * 0.45,
                       "remaining_area": left_w * bh * 0.45},
        "left_back":  {"x": ox, "y": oy + bh * 0.45, "w": left_w,
                       "h": bh * 0.55,
                       "remaining_area": left_w * bh * 0.55},
        "right_front": {"x": right_x, "y": oy, "w": right_w,
                        "h": bh * 0.45,
                        "remaining_area": right_w * bh * 0.45},
        "right_back":  {"x": right_x, "y": oy + bh * 0.55, "w": right_w,
                        "h": bh * 0.45,
                        "remaining_area": right_w * bh * 0.45},
        "top_right": {"x": ox, "y": oy + bh * 0.80, "w": left_w,
                      "h": bh * 0.20,
                      "remaining_area": left_w * bh * 0.20},
        "entrance": {"x": vert_x - 1.0, "y": oy + bh * 0.40,
                     "w": corridor_w + 1.0, "h": 2.2,
                     "remaining_area": (corridor_w + 1.0) * 2.2},
        "wet": {"x": right_x, "y": oy + bh * 0.45, "w": right_w,
                "h": bh * 0.55,
                "remaining_area": right_w * bh * 0.55},
    }

    return corridor, zones


def _create_t_corridor(bw, bh, ox, oy, entrance_side):
    """T-şekilli koridor — ortada dikey, ortada yatay kol."""
    corridor_w = 1.20

    # Dikey kol
    vert_x = ox + bw * 0.45 + random.random() * bw * 0.10
    vert_h = bh

    corridor = PlanRoom(
        name="Koridor", room_type="koridor",
        x=round(vert_x, 2), y=round(oy, 2),
        width=round(corridor_w, 2), height=round(vert_h, 2),
        has_exterior_wall=False,
    )

    left_w = vert_x - ox
    right_x = vert_x + corridor_w
    right_w = bw - (vert_x - ox + corridor_w)

    # T'nin yatay kolu bölge olarak
    t_cross_y = oy + bh * 0.50

    zones = {
        "corridor": {"x": vert_x, "y": oy, "w": corridor_w, "h": vert_h},
        "left_front": {"x": ox, "y": oy, "w": left_w, "h": bh * 0.50,
                       "remaining_area": left_w * bh * 0.50},
        "left_back":  {"x": ox, "y": t_cross_y, "w": left_w,
                       "h": bh * 0.50,
                       "remaining_area": left_w * bh * 0.50},
        "right_front": {"x": right_x, "y": oy, "w": right_w,
                        "h": bh * 0.35,
                        "remaining_area": right_w * bh * 0.35},
        "right_mid":   {"x": right_x, "y": oy + bh * 0.35, "w": right_w,
                        "h": bh * 0.30,
                        "remaining_area": right_w * bh * 0.30},
        "right_back":  {"x": right_x, "y": oy + bh * 0.65, "w": right_w,
                        "h": bh * 0.35,
                        "remaining_area": right_w * bh * 0.35},
        "entrance": {"x": vert_x - 1.2, "y": oy, "w": corridor_w + 1.2,
                     "h": 2.2,
                     "remaining_area": (corridor_w + 1.2) * 2.2},
        "wet": {"x": right_x, "y": oy + bh * 0.35, "w": right_w,
                "h": bh * 0.65,
                "remaining_area": right_w * bh * 0.65},
    }

    return corridor, zones


def _create_short_corridor(bw, bh, ox, oy, entrance_side):
    """Kısa koridor — kompakt düzen (1+1, 2+1 için ideal)."""
    corridor_w = 1.10
    corridor_h = bh * (0.35 + random.random() * 0.15)

    corr_x = ox + bw * (0.38 + random.random() * 0.15)
    corr_y = oy + (bh - corridor_h) * 0.5

    corridor = PlanRoom(
        name="Koridor", room_type="koridor",
        x=round(corr_x, 2), y=round(corr_y, 2),
        width=round(corridor_w, 2), height=round(corridor_h, 2),
        has_exterior_wall=False,
    )

    left_w = corr_x - ox
    right_x = corr_x + corridor_w
    right_w = bw - (corr_x - ox + corridor_w)

    zones = {
        "corridor": {"x": corr_x, "y": corr_y, "w": corridor_w,
                     "h": corridor_h},
        "left_front": {"x": ox, "y": oy, "w": left_w, "h": bh * 0.55,
                       "remaining_area": left_w * bh * 0.55},
        "left_back":  {"x": ox, "y": oy + bh * 0.55, "w": left_w,
                       "h": bh * 0.45,
                       "remaining_area": left_w * bh * 0.45},
        "right_front": {"x": right_x, "y": oy, "w": right_w,
                        "h": bh * 0.50,
                        "remaining_area": right_w * bh * 0.50},
        "right_back":  {"x": right_x, "y": oy + bh * 0.50, "w": right_w,
                        "h": bh * 0.50,
                        "remaining_area": right_w * bh * 0.50},
        "entrance": {"x": corr_x - 0.8, "y": oy, "w": corridor_w + 0.8,
                     "h": 2.0,
                     "remaining_area": (corridor_w + 0.8) * 2.0},
        "wet": {"x": right_x, "y": oy + bh * 0.50, "w": right_w,
                "h": bh * 0.50,
                "remaining_area": right_w * bh * 0.50},
    }

    return corridor, zones


def _create_open_plan_corridor(bw, bh, ox, oy, entrance_side):
    """Açık plan düzeni — geniş salon alanı, kısa koridor."""
    corridor_w = 1.10
    corridor_h = bh * 0.55

    corr_x = ox + bw * (0.55 + random.random() * 0.10)
    corr_y = oy + bh * 0.45

    corridor = PlanRoom(
        name="Koridor", room_type="koridor",
        x=round(corr_x, 2), y=round(corr_y, 2),
        width=round(corridor_w, 2), height=round(corridor_h, 2),
        has_exterior_wall=False,
    )

    left_w = corr_x - ox
    right_x = corr_x + corridor_w
    right_w = bw - (corr_x - ox + corridor_w)

    zones = {
        "corridor": {"x": corr_x, "y": corr_y, "w": corridor_w,
                     "h": corridor_h},
        # Salon + mutfak → büyük ön bölge
        "left_front": {"x": ox, "y": oy, "w": left_w, "h": bh * 0.50,
                       "remaining_area": left_w * bh * 0.50},
        "left_back":  {"x": ox, "y": oy + bh * 0.50, "w": left_w,
                       "h": bh * 0.50,
                       "remaining_area": left_w * bh * 0.50},
        "right_front": {"x": right_x, "y": oy, "w": right_w,
                        "h": bh * 0.45,
                        "remaining_area": right_w * bh * 0.45},
        "right_back":  {"x": right_x, "y": oy + bh * 0.55, "w": right_w,
                        "h": bh * 0.45,
                        "remaining_area": right_w * bh * 0.45},
        "entrance": {"x": corr_x - 1.0, "y": oy + bh * 0.40,
                     "w": corridor_w + 1.0, "h": 2.0,
                     "remaining_area": (corridor_w + 1.0) * 2.0},
        "wet": {"x": right_x, "y": oy + bh * 0.45, "w": right_w,
                "h": bh * 0.55,
                "remaining_area": right_w * bh * 0.55},
    }

    return corridor, zones
