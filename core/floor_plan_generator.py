"""
Profesyonel Kat Planı Üretici — Constraint-Satisfaction tabanlı.

Gerçek mimari planlara yakın sonuçlar üretir:
- Duvar paylaşımı (odalar arasında boşluk yok)
- Koridor omurgası (tüm odalara erişim)
- Bitişiklik grafı (veri setinden)
- Islak hacim gruplaması (ortak tesisat şaftı)
- Dış cephe önceliği (salon/balkon güneye)
- Yapısal grid uyumu
"""

import math
import random
from dataclasses import dataclass, field
from core.plan_scorer import FloorPlan, PlanRoom
from dataset.dataset_rules import (
    ROOM_SIZE_STATS, ROOM_ASPECT_RATIOS, ADJACENCY_PROBABILITY,
    ROOM_EXTERIOR_WALL_PRIORITY, ROOM_PLACEMENT_RULES,
    WET_AREA_CLUSTERING, calculate_ideal_dimensions,
)


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
) -> FloorPlan:
    """Profesyonel kalitede kat planı üretir.

    Algoritma:
    1. Odaları öncelik sırasına koy
    2. Koridor omurgasını yerleştir
    3. Islak hacimleri grupla ve yerleştir
    4. Salon/balkon güneş cephesine
    5. Yatak odaları kalan alanlara
    6. Boşlukları doldur, boyutları ayarla
    7. Kapı ve pencereleri ekle
    """
    if seed is not None:
        random.seed(seed)

    bw, bh = buildable_width, buildable_height
    ox, oy = origin_x, origin_y

    # ── Oda programını hazırla ──
    if room_program is None:
        room_program = _default_room_program(apartment_type, target_area)

    slots = _create_room_slots(room_program)

    # ── Koridor omurgası ──
    corridor_slot, layout_zones = _create_corridor_spine(bw, bh, ox, oy, entrance_side)

    # ── Odaları bölgelere yerleştir ──
    rooms = []

    # Koridor
    if corridor_slot:
        rooms.append(corridor_slot)

    # 1. Islak hacimleri grupla (ortak şaft bölgesine)
    wet_slots = [s for s in slots if s.is_wet]
    dry_slots = [s for s in slots if not s.is_wet and s.room_type != "koridor"]

    # Islak hacimler → şaft bölgesine (koridor yanı, iç cephe)
    wet_zone = layout_zones.get("wet", layout_zones.get("right_back", layout_zones.get("right")))
    if wet_zone and wet_slots:
        _place_rooms_in_zone(wet_slots, wet_zone, rooms, exterior_side="none")

    # 2. Salon + balkon → güneş cephesine
    sun_zone = _get_sun_zone(layout_zones, sun_direction, entrance_side)
    salon_slots = [s for s in dry_slots if s.room_type in ("salon", "balkon")]
    remaining_dry = [s for s in dry_slots if s.room_type not in ("salon", "balkon")]

    if sun_zone and salon_slots:
        _place_rooms_in_zone(salon_slots, sun_zone, rooms, exterior_side=sun_direction)

    # 3. Antre → giriş noktasına
    antre_slots = [s for s in remaining_dry if s.room_type == "antre"]
    remaining_dry = [s for s in remaining_dry if s.room_type != "antre"]
    if antre_slots:
        antre_zone = layout_zones.get("entrance", layout_zones.get("left_front", None))
        if antre_zone:
            _place_rooms_in_zone(antre_slots, antre_zone, rooms, exterior_side="none")

    # 4. Yatak odaları → kalan bölgelere
    bedroom_slots = [s for s in remaining_dry if s.room_type == "yatak_odasi"]
    other_slots = [s for s in remaining_dry if s.room_type != "yatak_odasi"]

    remaining_zones = [z for z_name, z in layout_zones.items()
                       if z_name not in ("corridor", "wet") and z.get("remaining_area", z["w"] * z["h"]) > 5]

    for slot in bedroom_slots + other_slots:
        if slot.placed:
            continue
        # En uygun bölgeyi bul
        best_zone = _find_best_zone(slot, remaining_zones)
        if best_zone:
            _place_single_room(slot, best_zone, rooms)

    # ── Yerleştirilmemiş odaları zorla yerleştir ──
    unplaced = [s for s in slots if not s.placed]
    if unplaced:
        _force_place_remaining(unplaced, rooms, bw, bh, ox, oy)

    # ── Kapı ve pencereleri ekle ──
    plan_rooms = _convert_to_plan_rooms(rooms, bw, bh, ox, oy, sun_direction, entrance_side)

    total_area = sum(r.area for r in plan_rooms)
    return FloorPlan(rooms=plan_rooms, total_area=total_area, apartment_type=apartment_type)


def _default_room_program(apt_type: str, target: float) -> list[dict]:
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
            ("Yatak Odası 2", "yatak_odasi", 0.11), ("Yatak Odası 3", "yatak_odasi", 0.09),
            ("Mutfak", "mutfak", 0.10), ("Banyo", "banyo", 0.055),
            ("WC", "wc", 0.025), ("Antre", "antre", 0.05),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.055),
        ],
        "4+1": [
            ("Salon", "salon", 0.21), ("Yatak Odası 1", "yatak_odasi", 0.11),
            ("Yatak Odası 2", "yatak_odasi", 0.10), ("Yatak Odası 3", "yatak_odasi", 0.08),
            ("Yatak Odası 4", "yatak_odasi", 0.08), ("Mutfak", "mutfak", 0.09),
            ("Banyo 1", "banyo", 0.05), ("Banyo 2", "banyo", 0.035),
            ("WC", "wc", 0.025), ("Antre", "antre", 0.04),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.05),
        ],
    }
    room_defs = programs.get(apt_type, programs["3+1"])
    return [{"isim": n, "tip": t, "m2": round(target * r, 1)} for n, t, r in room_defs]


def _create_room_slots(room_program: list[dict]) -> list[RoomSlot]:
    """Oda programından slot'lar oluşturur."""
    slots = []
    wet_types = {"banyo", "wc", "mutfak"}
    for rd in room_program:
        tip = rd.get("tip", "diger")
        if tip == "koridor":
            continue  # Koridor ayrıca oluşturulur
        slots.append(RoomSlot(
            name=rd.get("isim", "Oda"),
            room_type=tip,
            target_area=rd.get("m2", 10),
            priority=ROOM_EXTERIOR_WALL_PRIORITY.get(tip, 5),
            is_wet=tip in wet_types,
            min_width=1.5 if tip in ("wc",) else 2.0,
        ))
    return slots


def _create_corridor_spine(bw, bh, ox, oy, entrance_side):
    """Koridor omurgası ve yerleştirme bölgeleri oluşturur.

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
    corridor_w = 1.20  # Koridor genişliği

    # Koridor pozisyonu: genişliğin %35-%55 arasında rastgele (varyasyon)
    corr_ratio = 0.35 + random.random() * 0.20  # 0.35 — 0.55 arası
    corr_x = ox + bw * corr_ratio
    corr_y = oy
    corr_h = bh

    corridor = PlanRoom(
        name="Koridor", room_type="koridor",
        x=round(corr_x, 2), y=round(corr_y, 2),
        width=round(corridor_w, 2), height=round(corr_h, 2),
        has_exterior_wall=False,
    )

    # Yerleştirme bölgeleri — daire programına göre dinamik yükseklik
    left_w = corr_x - ox
    right_w = bw - (corr_x - ox + corridor_w)
    right_x = corr_x + corridor_w

    # Salon + balkon sol ön tarafta → yükseklikleri alan oranına göre
    # Varsayılan bölge dağılımları (daire programından bağımsız makul oranlar)
    zones = {
        "corridor": {"x": corr_x, "y": oy, "w": corridor_w, "h": bh},
        # Sol taraf — salon/balkon ön, yatak odaları arka
        "left_front": {"x": ox, "y": oy, "w": left_w, "h": bh * 0.50, "remaining_area": left_w * bh * 0.50},
        "left_back":  {"x": ox, "y": oy + bh * 0.50, "w": left_w, "h": bh * 0.50, "remaining_area": left_w * bh * 0.50},
        # Sağ taraf — mutfak ön, banyo/wc orta-arka
        "right_front": {"x": right_x, "y": oy, "w": right_w, "h": bh * 0.30, "remaining_area": right_w * bh * 0.30},
        "right_mid":   {"x": right_x, "y": oy + bh * 0.30, "w": right_w, "h": bh * 0.25, "remaining_area": right_w * bh * 0.25},
        "right_back":  {"x": right_x, "y": oy + bh * 0.55, "w": right_w, "h": bh * 0.45, "remaining_area": right_w * bh * 0.45},
        # Özel bölgeler
        "entrance":  {"x": corr_x - 1.2, "y": oy, "w": corridor_w + 1.2, "h": 2.2, "remaining_area": (corridor_w + 1.2) * 2.2},
        "wet":       {"x": right_x, "y": oy + bh * 0.30, "w": right_w, "h": bh * 0.70, "remaining_area": right_w * bh * 0.70},
    }

    return corridor, zones


def _get_sun_zone(zones, sun_dir, entrance_side):
    """Güneş yönüne göre en uygun bölgeyi döndürür."""
    # Güney güneş → ön cephe (y=min)
    if sun_dir in ("south", "güney"):
        return zones.get("left_front")
    elif sun_dir in ("north", "kuzey"):
        return zones.get("left_back")
    elif sun_dir in ("west", "batı"):
        return zones.get("left_front")
    else:
        return zones.get("left_front")


def _place_rooms_in_zone(slots: list[RoomSlot], zone: dict, rooms: list, exterior_side: str = ""):
    """Bir bölgeye birden fazla odayı sığdırarak yerleştirir.
    
    Küçük odalar (banyo, wc) bölgenin tam genişliğini almaz.
    """
    zx, zy = zone["x"], zone["y"]
    zw, zh = zone["w"], zone["h"]

    # Odaları alana göre büyükten küçüğe sırala
    slots.sort(key=lambda s: s.target_area, reverse=True)

    current_y = zy
    current_x = zx  # Yan yana yerleştirme için
    row_height = 0
    row_rooms = []

    for slot in slots:
        if slot.placed:
            continue

        remaining_h = zy + zh - current_y
        if remaining_h < slot.min_width:
            continue

        # Oda boyutlarını HEDEF ALANA göre hesapla
        ideal_w, ideal_h = calculate_ideal_dimensions(slot.room_type, slot.target_area)

        # Bölge genişliği oda için uygun mu?
        # ideal_w ile zone width karşılaştır
        use_full_width = (ideal_w >= zw * 0.7) or (slot.target_area >= 20.0)

        if not use_full_width:
            # Oda bölgenin tam genişliğini almaz
            room_w = min(ideal_w * 1.15, zw * 0.55)  # Biraz tolerans
            room_w = max(slot.min_width, room_w)
            room_h = slot.target_area / room_w
            room_h = max(slot.min_width, room_h)

            # Yan yana sığıyor mu?
            if current_x + room_w <= zx + zw + 0.1:
                pass  # Sığıyor
            else:
                # Yeni satıra geç
                current_y += row_height
                current_x = zx
                row_height = 0
                remaining_h = zy + zh - current_y
                if remaining_h < room_h:
                    continue
        else:
            # Büyük odalar → bölgenin tam genişliği
            room_w = zw
            room_h = slot.target_area / room_w if room_w > 0 else 3.0
            room_h = max(slot.min_width, min(room_h, remaining_h))

            # Önceki satırı kapat
            if current_x > zx + 0.1:
                current_y += row_height
                current_x = zx
                row_height = 0

            remaining_h = zy + zh - current_y
            room_h = min(room_h, remaining_h)

        # En-boy oranı kontrolü
        aspect = min(room_w, room_h) / max(room_w, room_h) if max(room_w, room_h) > 0 else 0.5
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
            # Dar oda — yan yana devam
            current_x += room_w
            row_height = max(row_height, room_h)
        else:
            # Büyük oda — alt satıra geç
            current_y += room_h
            current_x = zx
            row_height = 0

    # Kalan alanı güncelle
    zone["remaining_area"] = max(0, zw * (zy + zh - current_y - row_height))


def _place_single_room(slot: RoomSlot, zone: dict, rooms: list):
    """Tek bir odayı bölgeye yerleştirir."""
    _place_rooms_in_zone([slot], zone, rooms, exterior_side="")


def _find_best_zone(slot: RoomSlot, zones: list[dict]) -> dict | None:
    """Oda için en uygun bölgeyi seçer."""
    if not zones:
        return None

    # Yeterli alanı olan bölgeler
    valid = [z for z in zones if z.get("remaining_area", z["w"] * z["h"]) >= slot.target_area * 0.7]
    if not valid:
        valid = [z for z in zones if z.get("remaining_area", z["w"] * z["h"]) > 3]

    if not valid:
        return zones[0] if zones else None

    # Dış cephe gereken odalar → kenar bölgelere
    if slot.priority <= 3:
        valid.sort(key=lambda z: z.get("remaining_area", 0), reverse=True)
    else:
        # İç odalar → küçük bölgelere
        valid.sort(key=lambda z: abs(z.get("remaining_area", 0) - slot.target_area))

    return valid[0]


def _force_place_remaining(unplaced: list[RoomSlot], rooms: list, bw, bh, ox, oy):
    """Yerleştirilmemiş odaları boş alanlara zorla yerleştirir."""
    # Mevcut odaların kapladığı alanı analiz et
    occupied = set()
    grid_size = 0.5  # 50cm grid
    for r in rooms:
        for gx in range(int(r.x / grid_size), int((r.x + r.width) / grid_size) + 1):
            for gy in range(int(r.y / grid_size), int((r.y + r.height) / grid_size) + 1):
                occupied.add((gx, gy))

    for slot in unplaced:
        if slot.placed:
            continue

        # Boş alan bul
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

                # Çakışma kontrolü
                overlap = False
                for r in rooms:
                    if (x < r.x + r.width and x + w > r.x and
                        y < r.y + r.height and y + h > r.y):
                        overlap = True
                        break

                if not overlap:
                    # Skoru hesapla: mevcut odalara bitişik mi?
                    score = 0
                    for r in rooms:
                        if abs(x + w - r.x) < 0.1 or abs(x - (r.x + r.width)) < 0.1:
                            if y < r.y + r.height and y + h > r.y:
                                score += 10  # Yatay bitişik
                        if abs(y + h - r.y) < 0.1 or abs(y - (r.y + r.height)) < 0.1:
                            if x < r.x + r.width and x + w > r.x:
                                score += 10  # Dikey bitişik

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


def _convert_to_plan_rooms(rooms, bw, bh, ox, oy, sun_dir, entrance_side):
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

        # Cephe yönü
        if is_bottom:
            r.facing_direction = "south"
        elif is_top:
            r.facing_direction = "north"
        elif is_left:
            r.facing_direction = "west"
        elif is_right:
            r.facing_direction = "east"

        # ── Pencereler (dış duvarda olan odalar) ──
        r.windows = []
        if r.has_exterior_wall and r.room_type not in ("koridor", "antre"):
            if is_bottom:
                r.windows.append({"wall": "south", "position": 0.5, "width": min(1.6, r.width * 0.4)})
            elif is_top:
                r.windows.append({"wall": "north", "position": 0.5, "width": min(1.6, r.width * 0.4)})
            elif is_left:
                r.windows.append({"wall": "west", "position": 0.5, "width": min(1.4, r.height * 0.35)})
            elif is_right:
                r.windows.append({"wall": "east", "position": 0.5, "width": min(1.4, r.height * 0.35)})

            # Salon → 2 pencere
            if r.room_type == "salon" and r.area > 20 and len(r.windows) > 0:
                w = r.windows[0]
                r.windows = [
                    {**w, "position": 0.3, "width": min(1.4, r.width * 0.25)},
                    {**w, "position": 0.7, "width": min(1.4, r.width * 0.25)},
                ]

        # ── Kapılar ──
        r.doors = []
        # Koridora bakan duvardan kapı
        for other in rooms:
            if other is r or not isinstance(other, PlanRoom):
                continue
            if other.room_type != "koridor" and r.room_type != "koridor":
                continue

            # Yatay bitişiklik (yan yana)
            if abs(r.x + r.width - other.x) < 0.3 or abs(other.x + other.width - r.x) < 0.3:
                overlap_y = min(r.y + r.height, other.y + other.height) - max(r.y, other.y)
                if overlap_y > 0.9:
                    wall = "east" if r.x + r.width <= other.x + 0.3 else "west"
                    rel_pos = (max(r.y, other.y) + 0.5 - r.y) / r.height if r.height > 0 else 0.3
                    r.doors.append({"wall": wall, "position": max(0.15, min(0.85, rel_pos)), "width": 0.90})
                    break

            # Dikey bitişiklik (üst-alt)
            if abs(r.y + r.height - other.y) < 0.3 or abs(other.y + other.height - r.y) < 0.3:
                overlap_x = min(r.x + r.width, other.x + other.width) - max(r.x, other.x)
                if overlap_x > 0.9:
                    wall = "north" if r.y + r.height <= other.y + 0.3 else "south"
                    rel_pos = (max(r.x, other.x) + 0.5 - r.x) / r.width if r.width > 0 else 0.3
                    r.doors.append({"wall": wall, "position": max(0.15, min(0.85, rel_pos)), "width": 0.90})
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
    """Birden fazla plan alternatifi üretir (farklı seed ile)."""
    from core.plan_scorer import score_plan

    plans = []
    for i in range(plan_count * 3):  # 3× üret, en iyileri seç
        seed = random.randint(1, 100000)
        entrance_sides = ["south", "south", "west", "east"]
        entrance = entrance_sides[i % len(entrance_sides)]

        plan = generate_professional_plan(
            buildable_width, buildable_height, origin_x, origin_y,
            room_program, apartment_type, target_area,
            entrance_side=entrance, sun_direction=sun_direction,
            seed=seed,
        )

        if plan.rooms:
            sc = score_plan(plan, sun_best_direction=sun_direction)
            plans.append({
                "floor_plan": plan,
                "score": sc,
                "reasoning": f"Profesyonel plan (giriş: {entrance}, seed: {seed})",
                "seed": seed,
            })

    # Puana göre sırala
    plans.sort(key=lambda p: p["score"].total, reverse=True)
    return plans[:plan_count]
