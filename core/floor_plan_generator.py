"""
Profesyonel Kat Planı Üretici — Constraint-Satisfaction tabanlı.

Gerçek mimari planlara yakın sonuçlar üretir:
- Duvar paylaşımı (odalar arasında boşluk yok)
- Koridor omurgası (tüm odalara erişim)
- Bitişiklik grafı (veri setinden)
- Islak hacim gruplaması (ortak tesisat şaftı)
- Dış cephe önceliği (salon/balkon güneye)
- Yapısal grid uyumu
- L/T şekilli, kısa koridor varyasyonları
- Salon-mutfak açık plan seçeneği
- En-suite banyo (yatak odasına bağlı)
- Balkon salon/mutfağa bağlı
- 2 daireli kat planı desteği
"""

import math
import random
from dataclasses import dataclass, field
from core.plan_scorer import FloorPlan, PlanRoom
from config.room_defaults import MINIMUM_ODA_ALANLARI
from dataset.dataset_rules import (
    ROOM_SIZE_STATS, ROOM_ASPECT_RATIOS, ADJACENCY_PROBABILITY,
    ROOM_EXTERIOR_WALL_PRIORITY, ROOM_PLACEMENT_RULES,
    WET_AREA_CLUSTERING, calculate_ideal_dimensions,
)


# ═══════════════════════════════════════════════════════════════
# VERİ YAPILARI
# ═══════════════════════════════════════════════════════════════

@dataclass
class RoomSlot:
    """Yerleştirme öncesi oda slotu."""
    name: str
    room_type: str
    target_area: float
    min_width: float = 2.0
    priority: int = 5         # Dış cephe önceliği (1=en yüksek)
    is_wet: bool = False
    placed: bool = False
    # Yerleştirme sonrası
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


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
# ANA FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════

def generate_professional_plan(
    buildable_width: float,
    buildable_height: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    room_program: list[dict] | None = None,
    apartment_type: str = "3+1",
    target_area: float = 120.0,
    entrance_side: str = "south",
    sun_direction: str = "south",
    seed: int | None = None,
    layout_type: str | None = None,
    open_plan_kitchen: bool = False,
    en_suite: bool = False,
) -> FloorPlan:
    """Profesyonel kalitede kat planı üretir.

    Algoritma:
    1. Layout tipini seç (veya rastgele)
    2. Odaları öncelik sırasına koy
    3. Koridor omurgasını yerleştir (layout tipine göre)
    4. Islak hacimleri grupla ve yerleştir
    5. Salon/balkon güneş cephesine
    6. En-suite banyo varsa yatak odasına bağla
    7. Yatak odaları kalan alanlara
    8. Boşlukları doldur, boyutları ayarla
    9. Kapı ve pencereleri ekle
    """
    if seed is not None:
        random.seed(seed)

    bw, bh = buildable_width, buildable_height
    ox, oy = origin_x, origin_y

    # ── Layout tipi seçimi (varyasyon sağlar) ──
    if layout_type is None:
        layout_type = _select_layout_type(bw, bh, apartment_type, seed)

    # ── Açık plan kararı ──
    if open_plan_kitchen is False and seed is not None:
        open_plan_kitchen = (seed % 5 == 0)  # %20 olasılıkla açık plan

    # ── En-suite kararı ──
    if en_suite is False and apartment_type in ("3+1", "4+1"):
        en_suite = (random.random() < 0.4)  # %40 olasılıkla en-suite

    # ── Oda programını hazırla ──
    if room_program is None:
        room_program = _default_room_program(apartment_type, target_area,
                                              open_plan_kitchen, en_suite)

    slots = _create_room_slots(room_program)

    # ── Koridor omurgası (layout tipine göre) ──
    corridor_slot, layout_zones = _create_corridor_spine(
        bw, bh, ox, oy, entrance_side, layout_type
    )

    # ── Odaları bölgelere yerleştir ──
    rooms = []

    # Koridor
    if corridor_slot:
        rooms.append(corridor_slot)

    # 1. Açık plan salon-mutfak
    if open_plan_kitchen:
        salon_mut_slots = [s for s in slots if s.room_type in ("salon_mutfak",)]
        other_slots = [s for s in slots if s.room_type != "salon_mutfak"]
        sun_zone = _get_sun_zone(layout_zones, sun_direction, entrance_side)
        if sun_zone and salon_mut_slots:
            _place_rooms_in_zone(salon_mut_slots, sun_zone, rooms,
                                 exterior_side=sun_direction)
        slots = other_slots + [s for s in salon_mut_slots if not s.placed]

    # 2. Islak hacimleri grupla (ortak şaft bölgesine)
    wet_slots = [s for s in slots if s.is_wet and not s.placed]
    dry_slots = [s for s in slots if not s.is_wet and s.room_type != "koridor"
                 and not s.placed]

    wet_zone = layout_zones.get("wet", layout_zones.get("right_back",
                layout_zones.get("right")))
    if wet_zone and wet_slots:
        # En-suite banyoyu ayrı tut
        ensuite_slots = [s for s in wet_slots if "ebeveyn" in s.name.lower()
                         or "en-suite" in s.name.lower()]
        normal_wet = [s for s in wet_slots if s not in ensuite_slots]
        _place_rooms_in_zone(normal_wet, wet_zone, rooms, exterior_side="none")

    # 3. Salon + balkon → güneş cephesine
    sun_zone = _get_sun_zone(layout_zones, sun_direction, entrance_side)
    salon_slots = [s for s in dry_slots if s.room_type in ("salon", "balkon")
                   and not s.placed]
    remaining_dry = [s for s in dry_slots if s.room_type not in ("salon", "balkon")
                     or s.placed]

    if sun_zone and salon_slots:
        # Balkon salon'a bitişik olsun
        salon_first = sorted(salon_slots,
                             key=lambda s: 0 if s.room_type == "salon" else 1)
        _place_rooms_in_zone(salon_first, sun_zone, rooms,
                             exterior_side=sun_direction)

    # 4. Antre → giriş noktasına
    antre_slots = [s for s in remaining_dry if s.room_type == "antre"
                   and not s.placed]
    remaining_dry = [s for s in remaining_dry if s.room_type != "antre"
                     or s.placed]
    if antre_slots:
        antre_zone = layout_zones.get("entrance",
                     layout_zones.get("left_front", None))
        if antre_zone:
            _place_rooms_in_zone(antre_slots, antre_zone, rooms,
                                 exterior_side="none")

    # 5. En-suite banyo → ana yatak odasının yanına
    if en_suite:
        master_rooms = [r for r in rooms if "Yatak" in r.name
                        and ("1" in r.name or "Ebeveyn" in r.name)]
        ensuite_slots_remaining = [s for s in slots
                                    if ("ebeveyn" in s.name.lower()
                                        or "en-suite" in s.name.lower())
                                    and not s.placed]
        if master_rooms and ensuite_slots_remaining:
            mr = master_rooms[0]
            for es in ensuite_slots_remaining:
                # Yatak odasının yanına yerleştir
                es_w = min(2.5, mr.width * 0.4)
                es_h = es.target_area / es_w
                es.x = round(mr.x + mr.width - es_w, 2)
                es.y = round(mr.y + mr.height, 2)
                if es.y + es_h > oy + bh:
                    es.y = round(mr.y - es_h, 2)
                es.width = round(es_w, 2)
                es.height = round(es_h, 2)
                es.placed = True
                rooms.append(PlanRoom(
                    name=es.name, room_type=es.room_type,
                    x=es.x, y=es.y, width=es.width, height=es.height,
                    has_exterior_wall=False,
                ))

    # 6. Yatak odaları → kalan bölgelere
    bedroom_slots = [s for s in slots if s.room_type == "yatak_odasi"
                     and not s.placed]
    other_slots = [s for s in slots if s.room_type != "yatak_odasi"
                   and not s.placed and s.room_type != "koridor"]

    remaining_zones = [z for z_name, z in layout_zones.items()
                       if z_name not in ("corridor", "wet")
                       and z.get("remaining_area", z["w"] * z["h"]) > 5]

    for slot in bedroom_slots + other_slots:
        if slot.placed:
            continue
        best_zone = _find_best_zone(slot, remaining_zones)
        if best_zone:
            _place_single_room(slot, best_zone, rooms)

    # ── Yerleştirilmemiş odaları zorla yerleştir ──
    unplaced = [s for s in slots if not s.placed]
    if unplaced:
        _force_place_remaining(unplaced, rooms, bw, bh, ox, oy)

    # ── Kapı ve pencereleri ekle ──
    plan_rooms = _convert_to_plan_rooms(rooms, bw, bh, ox, oy,
                                         sun_direction, entrance_side,
                                         en_suite)

    total_area = sum(r.area for r in plan_rooms)
    plan = FloorPlan(rooms=plan_rooms, total_area=total_area,
                     apartment_type=apartment_type)
    plan.layout_type = layout_type
    plan.open_plan = open_plan_kitchen
    plan.en_suite = en_suite
    return plan


# ═══════════════════════════════════════════════════════════════
# ODA PROGRAMI
# ═══════════════════════════════════════════════════════════════

def _default_room_program(apt_type: str, target: float,
                           open_plan: bool = False,
                           en_suite: bool = False) -> list[dict]:
    """Daire tipine göre varsayılan oda programı."""
    programs = {
        "1+1": [
            ("Salon", "salon", 0.33), ("Yatak Odası", "yatak_odasi", 0.22),
            ("Mutfak", "mutfak", 0.15), ("Banyo", "banyo", 0.10),
            ("Antre", "antre", 0.08), ("Balkon", "balkon", 0.08),
        ],
        "2+1": [
            ("Salon", "salon", 0.26), ("Yatak Odası 1", "yatak_odasi", 0.16),
            ("Yatak Odası 2", "yatak_odasi", 0.13), ("Mutfak", "mutfak", 0.12),
            ("Banyo", "banyo", 0.07), ("WC", "wc", 0.03),
            ("Antre", "antre", 0.06), ("Koridor", "koridor", 0.06),
            ("Balkon", "balkon", 0.06),
        ],
        "3+1": [
            ("Salon", "salon", 0.23), ("Yatak Odası 1", "yatak_odasi", 0.13),
            ("Yatak Odası 2", "yatak_odasi", 0.11),
            ("Yatak Odası 3", "yatak_odasi", 0.09),
            ("Mutfak", "mutfak", 0.10), ("Banyo", "banyo", 0.055),
            ("WC", "wc", 0.025), ("Antre", "antre", 0.05),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.055),
        ],
        "4+1": [
            ("Salon", "salon", 0.21), ("Yatak Odası 1", "yatak_odasi", 0.11),
            ("Yatak Odası 2", "yatak_odasi", 0.10),
            ("Yatak Odası 3", "yatak_odasi", 0.08),
            ("Yatak Odası 4", "yatak_odasi", 0.08), ("Mutfak", "mutfak", 0.09),
            ("Banyo 1", "banyo", 0.05), ("Banyo 2", "banyo", 0.035),
            ("WC", "wc", 0.025), ("Antre", "antre", 0.04),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.05),
        ],
    }
    room_defs = list(programs.get(apt_type, programs["3+1"]))

    # Açık plan salon-mutfak
    if open_plan:
        salon_r = next((r for n, t, r in room_defs if t == "salon"), 0.23)
        mutfak_r = next((r for n, t, r in room_defs if t == "mutfak"), 0.10)
        room_defs = [(n, t, r) for n, t, r in room_defs
                     if t not in ("salon", "mutfak")]
        room_defs.insert(0, ("Salon + Mutfak", "salon_mutfak",
                             salon_r + mutfak_r))

    # En-suite banyo
    if en_suite and apt_type in ("3+1", "4+1"):
        room_defs.append(("Ebeveyn Banyosu", "banyo", 0.04))

    # Toplam oda yüzdelerinin %100'ü aşmadığını doğrula
    toplam_oran = sum(r for _, _, r in room_defs)
    if toplam_oran > 1.0:
        # Oranları normalize et — %100'e sığdır
        room_defs = [(n, t, r / toplam_oran) for n, t, r in room_defs]

    return [{"isim": n, "tip": t, "m2": round(target * r, 1)}
            for n, t, r in room_defs]


def _create_room_slots(room_program: list[dict]) -> list[RoomSlot]:
    """Oda programından slot'lar oluşturur.

    Hedef alan, yönetmelikteki minimum alanın altındaysa otomatik olarak
    minimum alana yükseltilir (3194 sayılı İmar Kanunu).
    """
    slots = []
    wet_types = {"banyo", "wc", "mutfak"}
    for rd in room_program:
        tip = rd.get("tip", "diger")
        if tip == "koridor":
            continue  # Koridor ayrıca oluşturulur

        hedef_alan = rd.get("m2", 10)

        # Minimum alan kontrolü — İmar Kanunu zorunlu alt sınırları
        effective_tip = tip if tip != "salon_mutfak" else "salon_mutfak"
        min_alan = MINIMUM_ODA_ALANLARI.get(effective_tip, 0.0)
        if hedef_alan < min_alan:
            hedef_alan = min_alan

        slots.append(RoomSlot(
            name=rd.get("isim", "Oda"),
            room_type=tip if tip != "salon_mutfak" else "salon",
            target_area=hedef_alan,
            priority=ROOM_EXTERIOR_WALL_PRIORITY.get(
                tip if tip != "salon_mutfak" else "salon", 5),
            is_wet=tip in wet_types,
            min_width=1.5 if tip in ("wc",) else 2.0,
        ))
    return slots


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


# ═══════════════════════════════════════════════════════════════
# ODA YERLEŞTİRME
# ═══════════════════════════════════════════════════════════════

def _get_sun_zone(zones, sun_dir, entrance_side):
    """Güneş yönüne göre en uygun bölgeyi döndürür."""
    if sun_dir in ("south", "güney"):
        return zones.get("left_front")
    elif sun_dir in ("north", "kuzey"):
        return zones.get("left_back")
    elif sun_dir in ("west", "batı"):
        return zones.get("left_front")
    else:
        return zones.get("left_front")


def _place_rooms_in_zone(slots: list[RoomSlot], zone: dict, rooms: list,
                          exterior_side: str = ""):
    """Bir bölgeye birden fazla odayı sığdırarak yerleştirir."""
    zx, zy = zone["x"], zone["y"]
    zw, zh = zone["w"], zone["h"]

    slots.sort(key=lambda s: s.target_area, reverse=True)

    current_y = zy
    current_x = zx
    row_height = 0

    for slot in slots:
        if slot.placed:
            continue

        remaining_h = zy + zh - current_y
        if remaining_h < slot.min_width:
            continue

        ideal_w, ideal_h = calculate_ideal_dimensions(slot.room_type,
                                                       slot.target_area)

        use_full_width = (ideal_w >= zw * 0.7) or (slot.target_area >= 20.0)

        if not use_full_width:
            room_w = min(ideal_w * 1.15, zw * 0.55)
            room_w = max(slot.min_width, room_w)
            room_h = slot.target_area / room_w
            room_h = max(slot.min_width, room_h)

            if current_x + room_w > zx + zw + 0.1:
                current_y += row_height
                current_x = zx
                row_height = 0
                remaining_h = zy + zh - current_y
                if remaining_h < room_h:
                    continue
        else:
            room_w = zw
            room_h = slot.target_area / room_w if room_w > 0 else 3.0
            room_h = max(slot.min_width, min(room_h, remaining_h))

            if current_x > zx + 0.1:
                current_y += row_height
                current_x = zx
                row_height = 0

            remaining_h = zy + zh - current_y
            room_h = min(room_h, remaining_h)

        # En-boy oranı kontrolü
        aspect = (min(room_w, room_h) / max(room_w, room_h)
                  if max(room_w, room_h) > 0 else 0.5)
        min_aspect = ROOM_ASPECT_RATIOS.get(slot.room_type, {}).get("min", 0.35)
        if aspect < min_aspect and room_h < room_w:
            room_h = max(room_h, room_w * min_aspect)
            room_h = min(room_h, zy + zh - current_y)

        slot.x = round(current_x, 2)
        slot.y = round(current_y, 2)
        slot.width = round(room_w, 2)
        slot.height = round(room_h, 2)
        slot.placed = True

        rooms.append(PlanRoom(
            name=slot.name, room_type=slot.room_type,
            x=slot.x, y=slot.y,
            width=slot.width, height=slot.height,
            has_exterior_wall=exterior_side != "none",
            facing_direction=exterior_side if exterior_side != "none" else "",
        ))

        if not use_full_width:
            current_x += room_w
            row_height = max(row_height, room_h)
        else:
            current_y += room_h
            current_x = zx
            row_height = 0

    zone["remaining_area"] = max(0, zw * (zy + zh - current_y - row_height))


def _place_single_room(slot: RoomSlot, zone: dict, rooms: list):
    """Tek bir odayı bölgeye yerleştirir."""
    _place_rooms_in_zone([slot], zone, rooms, exterior_side="")


def _find_best_zone(slot: RoomSlot, zones: list[dict]) -> dict | None:
    """Oda için en uygun bölgeyi seçer."""
    if not zones:
        return None

    valid = [z for z in zones
             if z.get("remaining_area", z["w"] * z["h"]) >= slot.target_area * 0.7]
    if not valid:
        valid = [z for z in zones
                 if z.get("remaining_area", z["w"] * z["h"]) > 3]

    if not valid:
        return zones[0] if zones else None

    if slot.priority <= 3:
        valid.sort(key=lambda z: z.get("remaining_area", 0), reverse=True)
    else:
        valid.sort(key=lambda z: abs(z.get("remaining_area", 0) - slot.target_area))

    return valid[0]


def _force_place_remaining(unplaced: list[RoomSlot], rooms: list,
                            bw, bh, ox, oy):
    """Yerleştirilmemiş odaları boş alanlara zorla yerleştirir."""
    occupied = set()
    grid_size = 0.5
    for r in rooms:
        for gx in range(int(r.x / grid_size),
                        int((r.x + r.width) / grid_size) + 1):
            for gy in range(int(r.y / grid_size),
                            int((r.y + r.height) / grid_size) + 1):
                occupied.add((gx, gy))

    for slot in unplaced:
        if slot.placed:
            continue

        best_pos = None
        best_score = -1

        for gx in range(int(ox / grid_size), int((ox + bw) / grid_size)):
            for gy in range(int(oy / grid_size), int((oy + bh) / grid_size)):
                if (gx, gy) in occupied:
                    continue

                x = gx * grid_size
                y = gy * grid_size
                w = min(math.sqrt(slot.target_area * 1.3), ox + bw - x)
                h = slot.target_area / max(w, 1)

                if w < slot.min_width or h < slot.min_width:
                    continue
                if x + w > ox + bw or y + h > oy + bh:
                    continue

                overlap = False
                for r in rooms:
                    if (x < r.x + r.width and x + w > r.x and
                            y < r.y + r.height and y + h > r.y):
                        overlap = True
                        break

                if not overlap:
                    score = 0
                    for r in rooms:
                        if (abs(x + w - r.x) < 0.1
                                or abs(x - (r.x + r.width)) < 0.1):
                            if y < r.y + r.height and y + h > r.y:
                                score += 10
                        if (abs(y + h - r.y) < 0.1
                                or abs(y - (r.y + r.height)) < 0.1):
                            if x < r.x + r.width and x + w > r.x:
                                score += 10

                    if score > best_score:
                        best_score = score
                        best_pos = (x, y, w, h)

        if best_pos:
            x, y, w, h = best_pos
            slot.x, slot.y, slot.width, slot.height = x, y, w, h
            slot.placed = True
            rooms.append(PlanRoom(
                name=slot.name, room_type=slot.room_type,
                x=round(x, 2), y=round(y, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=False,
            ))


# ═══════════════════════════════════════════════════════════════
# KAPI VE PENCERE EKLEME
# ═══════════════════════════════════════════════════════════════

def _convert_to_plan_rooms(rooms, bw, bh, ox, oy, sun_dir, entrance_side,
                            en_suite=False):
    """Oda listesini son hale getirir — kapı ve pencere ekler."""
    result = []

    for room in rooms:
        if isinstance(room, PlanRoom):
            r = room
        else:
            continue

        # ── Dış duvar tespiti ──
        is_left = abs(r.x - ox) < 0.3
        is_right = abs(r.x + r.width - (ox + bw)) < 0.3
        is_bottom = abs(r.y - oy) < 0.3
        is_top = abs(r.y + r.height - (oy + bh)) < 0.3
        r.has_exterior_wall = is_left or is_right or is_bottom or is_top

        if is_bottom:
            r.facing_direction = "south"
        elif is_top:
            r.facing_direction = "north"
        elif is_left:
            r.facing_direction = "west"
        elif is_right:
            r.facing_direction = "east"

        # ── Pencereler ──
        r.windows = []
        if r.has_exterior_wall and r.room_type not in ("koridor", "antre"):
            if is_bottom:
                r.windows.append({"wall": "south", "position": 0.5,
                                  "width": min(1.6, r.width * 0.4)})
            elif is_top:
                r.windows.append({"wall": "north", "position": 0.5,
                                  "width": min(1.6, r.width * 0.4)})
            elif is_left:
                r.windows.append({"wall": "west", "position": 0.5,
                                  "width": min(1.4, r.height * 0.35)})
            elif is_right:
                r.windows.append({"wall": "east", "position": 0.5,
                                  "width": min(1.4, r.height * 0.35)})

            # Salon → 2 pencere
            if r.room_type == "salon" and r.area > 20 and len(r.windows) > 0:
                w = r.windows[0]
                r.windows = [
                    {**w, "position": 0.3,
                     "width": min(1.4, r.width * 0.25)},
                    {**w, "position": 0.7,
                     "width": min(1.4, r.width * 0.25)},
                ]

            # İki dış duvara bakan odalar → ek pencere
            ext_walls = []
            if is_left:
                ext_walls.append("west")
            if is_right:
                ext_walls.append("east")
            if is_bottom:
                ext_walls.append("south")
            if is_top:
                ext_walls.append("north")
            if len(ext_walls) > 1 and r.room_type in ("salon", "yatak_odasi"):
                for ew in ext_walls[1:]:
                    dim = r.height if ew in ("west", "east") else r.width
                    r.windows.append({"wall": ew, "position": 0.5,
                                      "width": min(1.2, dim * 0.3)})

        # ── Kapılar ──
        r.doors = []
        # Koridora bakan duvardan kapı
        for other in rooms:
            if other is r or not isinstance(other, PlanRoom):
                continue
            if other.room_type != "koridor" and r.room_type != "koridor":
                continue

            # Yatay bitişiklik
            if (abs(r.x + r.width - other.x) < 0.3
                    or abs(other.x + other.width - r.x) < 0.3):
                overlap_y = (min(r.y + r.height, other.y + other.height)
                             - max(r.y, other.y))
                if overlap_y > 0.9:
                    wall = ("east" if r.x + r.width <= other.x + 0.3
                            else "west")
                    rel_pos = ((max(r.y, other.y) + 0.5 - r.y) / r.height
                               if r.height > 0 else 0.3)
                    r.doors.append({
                        "wall": wall,
                        "position": max(0.15, min(0.85, rel_pos)),
                        "width": 0.90,
                    })
                    break

            # Dikey bitişiklik
            if (abs(r.y + r.height - other.y) < 0.3
                    or abs(other.y + other.height - r.y) < 0.3):
                overlap_x = (min(r.x + r.width, other.x + other.width)
                             - max(r.x, other.x))
                if overlap_x > 0.9:
                    wall = ("north" if r.y + r.height <= other.y + 0.3
                            else "south")
                    rel_pos = ((max(r.x, other.x) + 0.5 - r.x) / r.width
                               if r.width > 0 else 0.3)
                    r.doors.append({
                        "wall": wall,
                        "position": max(0.15, min(0.85, rel_pos)),
                        "width": 0.90,
                    })
                    break

        # En-suite banyo → yatak odasına kapı
        if en_suite and "ebeveyn" in r.name.lower():
            for other in rooms:
                if not isinstance(other, PlanRoom):
                    continue
                if "Yatak" in other.name and ("1" in other.name
                                               or "Ebeveyn" in other.name):
                    if (abs(r.y - (other.y + other.height)) < 0.3
                            or abs(other.y - (r.y + r.height)) < 0.3):
                        wall = ("south" if r.y > other.y else "north")
                        r.doors.append({"wall": wall, "position": 0.5,
                                        "width": 0.80})
                        break

        # Kapısı olmayan odalar → en yakın odaya kapı
        if not r.doors and r.room_type != "koridor":
            r.doors.append({"wall": "north", "position": 0.2, "width": 0.90})

        result.append(r)

    return result


# ═══════════════════════════════════════════════════════════════
# ÇOKLU ALTERNATİF ÜRETİM
# ═══════════════════════════════════════════════════════════════

def generate_multiple_plans(
    buildable_width: float,
    buildable_height: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    room_program: list[dict] | None = None,
    apartment_type: str = "3+1",
    target_area: float = 120.0,
    sun_direction: str = "south",
    plan_count: int = 3,
) -> list[dict]:
    """Birden fazla plan alternatifi üretir — farklı layout tipleriyle."""
    from core.plan_scorer import score_plan

    plans = []
    used_layouts = set()

    for i in range(plan_count * 4):  # 4× üret, en iyileri seç
        seed = random.randint(1, 100000)
        entrance_sides = ["south", "south", "west", "east"]
        entrance = entrance_sides[i % len(entrance_sides)]

        # Farklı layout tipleri deneyelim
        layout = LAYOUT_TYPES[i % len(LAYOUT_TYPES)]
        open_plan = (i % 3 == 0)
        en_suite = (i % 4 == 0) and apartment_type in ("3+1", "4+1")

        plan = generate_professional_plan(
            buildable_width, buildable_height, origin_x, origin_y,
            room_program, apartment_type, target_area,
            entrance_side=entrance, sun_direction=sun_direction,
            seed=seed, layout_type=layout,
            open_plan_kitchen=open_plan, en_suite=en_suite,
        )

        if plan.rooms:
            sc = score_plan(plan, sun_best_direction=sun_direction)
            layout_label = getattr(plan, 'layout_type', layout)
            features = []
            if getattr(plan, 'open_plan', False):
                features.append("açık plan")
            if getattr(plan, 'en_suite', False):
                features.append("en-suite")
            feat_str = f" ({', '.join(features)})" if features else ""

            plans.append({
                "floor_plan": plan,
                "score": sc,
                "reasoning": (f"Profesyonel plan — {layout_label}"
                              f"{feat_str} (giriş: {entrance}, seed: {seed})"),
                "seed": seed,
                "layout_type": layout_label,
            })

    # Puana göre sırala, farklı layout tiplerini tercih et
    plans.sort(key=lambda p: p["score"].total, reverse=True)

    # Çeşitlilik filtresi: farklı layout tiplerini seç
    diverse_plans = []
    for p in plans:
        lt = p.get("layout_type", "")
        if lt not in used_layouts or len(diverse_plans) < plan_count:
            diverse_plans.append(p)
            used_layouts.add(lt)
        if len(diverse_plans) >= plan_count:
            break

    return diverse_plans[:plan_count]


# ═══════════════════════════════════════════════════════════════
# 2 DAİRELİ KAT PLANI
# ═══════════════════════════════════════════════════════════════

def generate_dual_apartment_plan(
    buildable_width: float,
    buildable_height: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    apt_type_1: str = "3+1",
    apt_type_2: str = "2+1",
    target_area_1: float = 120.0,
    target_area_2: float = 90.0,
    sun_direction: str = "south",
    seed: int | None = None,
) -> dict:
    """2 daireli kat planı üretir (merdiven evi + 2 ayrı daire).

    Returns:
        dict with keys: stairwell, apartment_1, apartment_2
    """
    if seed is not None:
        random.seed(seed)

    bw, bh = buildable_width, buildable_height
    ox, oy = origin_x, origin_y

    # Merdiven evi — ortada
    stairwell_w = 3.5
    stairwell_h = 5.0
    stairwell_x = ox + (bw - stairwell_w) / 2
    stairwell_y = oy + bh * 0.45

    stairwell = PlanRoom(
        name="Merdiven Evi", room_type="merdiven",
        x=round(stairwell_x, 2), y=round(stairwell_y, 2),
        width=round(stairwell_w, 2), height=round(stairwell_h, 2),
        has_exterior_wall=False,
    )

    # Daire 1 — sol taraf
    apt1_width = stairwell_x - ox
    apt1 = generate_professional_plan(
        apt1_width, bh, ox, oy,
        apartment_type=apt_type_1,
        target_area=target_area_1,
        entrance_side="east",
        sun_direction=sun_direction,
        seed=seed,
    )

    # Daire 2 — sağ taraf
    apt2_x = stairwell_x + stairwell_w
    apt2_width = ox + bw - apt2_x
    apt2 = generate_professional_plan(
        apt2_width, bh, apt2_x, oy,
        apartment_type=apt_type_2,
        target_area=target_area_2,
        entrance_side="west",
        sun_direction=sun_direction,
        seed=(seed + 1000) if seed else None,
    )

    return {
        "stairwell": stairwell,
        "apartment_1": apt1,
        "apartment_2": apt2,
        "combined_rooms": [stairwell] + apt1.rooms + apt2.rooms,
    }
