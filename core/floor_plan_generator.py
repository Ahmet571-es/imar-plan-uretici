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

import logging
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
# ALT MODÜLLERDEN İÇE AKTARIMLAR
# (Geriye dönük uyumluluk: bu modülden yapılan tüm import'lar çalışmaya
#  devam eder.)
# ═══════════════════════════════════════════════════════════════

from core.geometry.room_slots import RoomSlot, _create_room_slots, _default_room_program  # noqa: F401,E501
from core.geometry.corridor_layouts import (  # noqa: F401
    LAYOUT_TYPES,
    _select_layout_type,
    _create_corridor_spine,
    _create_center_corridor,
    _create_l_corridor,
    _create_t_corridor,
    _create_short_corridor,
    _create_open_plan_corridor,
)
from core.geometry.room_placement import (  # noqa: F401
    _get_sun_zone,
    _place_rooms_in_zone,
    _place_single_room,
    _find_best_zone,
    _force_place_remaining,
)
from core.geometry.plan_finalization import _convert_to_plan_rooms  # noqa: F401


logger = logging.getLogger(__name__)  # noqa: E305

# Islak hacim tipleri (banyo, wc, mutfak)
_ISLAK_HACIM_TIPLERI = {"banyo", "wc", "mutfak"}
# Islak hacimler arası maksimum mesafe eşiği (metre)
_ISLAK_HACIM_MAX_MESAFE = 5.0


def _verify_wet_area_proximity(rooms) -> None:  # noqa: E302
    """Islak hacimlerin (banyo, wc, mutfak) ortak tesisat şaft bölgesine
    yakınlığını doğrular.

    Yerleştirme sonrası çağrılır. Islak hacimler arası merkez-merkez mesafe
    5 metreyi aşıyorsa uyarı loglar.
    """
    islak_odalar = [r for r in rooms
                    if isinstance(r, PlanRoom) and r.room_type in _ISLAK_HACIM_TIPLERI]

    if len(islak_odalar) < 2:
        return

    max_mesafe = 0.0
    en_uzak_cift = ("", "")

    for i, r1 in enumerate(islak_odalar):
        for r2 in islak_odalar[i + 1:]:
            dx = (r1.x + r1.width / 2) - (r2.x + r2.width / 2)
            dy = (r1.y + r1.height / 2) - (r2.y + r2.height / 2)
            mesafe = math.sqrt(dx * dx + dy * dy)
            if mesafe > max_mesafe:
                max_mesafe = mesafe
                en_uzak_cift = (r1.name, r2.name)

    if max_mesafe > _ISLAK_HACIM_MAX_MESAFE:
        logger.debug(
            "Islak hacim yakınlık: %s ile %s arası %.1f m (eşik: %.1f m)",
            en_uzak_cift[0], en_uzak_cift[1], max_mesafe, _ISLAK_HACIM_MAX_MESAFE
        )


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

    # ── Islak hacim yakınlık kontrolü (yerleştirme sonrası) ──
    _verify_wet_area_proximity(rooms)

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
