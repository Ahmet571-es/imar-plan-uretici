"""
Oda yerleştirme — bölgelere oda yerleştirme, güneş cephesi ve zorla yerleştirme.
"""

import math
from core.plan_scorer import PlanRoom
from core.geometry.room_slots import RoomSlot
from dataset.dataset_rules import (
    ROOM_ASPECT_RATIOS,
    calculate_ideal_dimensions,
)


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


def _place_wet_rooms_adjacent(wet_slots: list[RoomSlot], zone: dict,
                               rooms: list):
    """Islak hacimleri (mutfak, banyo, wc) bitişik olarak yerleştirir.

    Ortak tesisat şaftı oluşturmak için ıslak hacimler yan yana veya
    üst üste dizilir. Sıralama: mutfak -> banyo -> wc.
    Mutfak üst üste, banyo ve wc yan yana yerleştirilir (duvar paylaşımı).
    """
    if not wet_slots:
        return

    zx, zy = zone["x"], zone["y"]
    zw, zh = zone["w"], zone["h"]

    # Islak hacimleri öncelik sırasına koy: mutfak > banyo > wc
    tip_oncelik = {"mutfak": 0, "banyo": 1, "wc": 2}
    wet_slots.sort(key=lambda s: tip_oncelik.get(s.room_type, 9))

    # Banyo ve WC'yi yan yana yerleştirmek için ayır
    banyo_slot = None
    wc_slot = None
    mutfak_slot = None
    diger_slots = []

    for s in wet_slots:
        if s.placed:
            continue
        if s.room_type == "banyo" and banyo_slot is None:
            banyo_slot = s
        elif s.room_type == "wc" and wc_slot is None:
            wc_slot = s
        elif s.room_type == "mutfak" and mutfak_slot is None:
            mutfak_slot = s
        else:
            diger_slots.append(s)

    current_y = zy

    # Önce mutfak — bölge genişliğinde üste yerleşir
    if mutfak_slot and not mutfak_slot.placed:
        remaining_h = zy + zh - current_y
        if remaining_h >= mutfak_slot.min_width:
            room_w = zw
            room_h = mutfak_slot.target_area / room_w if room_w > 0 else 3.0
            room_h = max(mutfak_slot.min_width, min(room_h, remaining_h))

            # En-boy oranı kontrolü
            aspect = (min(room_w, room_h) / max(room_w, room_h)
                      if max(room_w, room_h) > 0 else 0.5)
            min_aspect = ROOM_ASPECT_RATIOS.get("mutfak", {}).get("min", 0.35)
            if aspect < min_aspect and room_h < room_w:
                room_h = max(room_h, room_w * min_aspect)
                room_h = min(room_h, zy + zh - current_y)

            mutfak_slot.x = round(zx, 2)
            mutfak_slot.y = round(current_y, 2)
            mutfak_slot.width = round(room_w, 2)
            mutfak_slot.height = round(room_h, 2)
            mutfak_slot.placed = True

            rooms.append(PlanRoom(
                name=mutfak_slot.name, room_type=mutfak_slot.room_type,
                x=mutfak_slot.x, y=mutfak_slot.y,
                width=mutfak_slot.width, height=mutfak_slot.height,
                has_exterior_wall=False, facing_direction="",
            ))
            current_y += room_h

    # Banyo ve WC yan yana — mutfağın hemen altına, duvar paylaşarak
    if banyo_slot and wc_slot and not banyo_slot.placed and not wc_slot.placed:
        remaining_h = zy + zh - current_y
        toplam_alan = banyo_slot.target_area + wc_slot.target_area

        if remaining_h >= 2.0 and zw >= 2.4:
            # Banyo ve WC'yi yan yana yerleştir — genişliği alana göre böl
            banyo_oran = banyo_slot.target_area / toplam_alan
            banyo_w = max(banyo_slot.min_width, zw * banyo_oran)
            wc_w = max(wc_slot.min_width, zw - banyo_w)

            # Genişlikler bölgeye sığmıyorsa oranla düzelt
            if banyo_w + wc_w > zw:
                oran = zw / (banyo_w + wc_w)
                banyo_w *= oran
                wc_w *= oran

            banyo_h = banyo_slot.target_area / banyo_w if banyo_w > 0 else 2.5
            wc_h = wc_slot.target_area / wc_w if wc_w > 0 else 2.0

            # Her ikisi de kalan yüksekliğe sığmalı
            banyo_h = max(banyo_slot.min_width, min(banyo_h, remaining_h))
            wc_h = max(wc_slot.min_width, min(wc_h, remaining_h))

            # Aynı yükseklikte hizala (daha düzenli görünüm)
            ortak_h = max(banyo_h, wc_h)
            ortak_h = min(ortak_h, remaining_h)

            # Banyo — sol taraf
            banyo_slot.x = round(zx, 2)
            banyo_slot.y = round(current_y, 2)
            banyo_slot.width = round(banyo_w, 2)
            banyo_slot.height = round(ortak_h, 2)
            banyo_slot.placed = True

            rooms.append(PlanRoom(
                name=banyo_slot.name, room_type=banyo_slot.room_type,
                x=banyo_slot.x, y=banyo_slot.y,
                width=banyo_slot.width, height=banyo_slot.height,
                has_exterior_wall=False, facing_direction="",
            ))

            # WC — banyonun hemen sağında (duvar paylaşarak)
            wc_slot.x = round(zx + banyo_w, 2)
            wc_slot.y = round(current_y, 2)
            wc_slot.width = round(wc_w, 2)
            wc_slot.height = round(ortak_h, 2)
            wc_slot.placed = True

            rooms.append(PlanRoom(
                name=wc_slot.name, room_type=wc_slot.room_type,
                x=wc_slot.x, y=wc_slot.y,
                width=wc_slot.width, height=wc_slot.height,
                has_exterior_wall=False, facing_direction="",
            ))

            current_y += ortak_h
        else:
            # Yer yetersiz — üst üste yerleştir (eski yöntem)
            for slot in [banyo_slot, wc_slot]:
                if slot.placed:
                    continue
                rem = zy + zh - current_y
                if rem < slot.min_width:
                    continue
                room_w = zw
                room_h = slot.target_area / room_w if room_w > 0 else 2.5
                room_h = max(slot.min_width, min(room_h, rem))

                slot.x = round(zx, 2)
                slot.y = round(current_y, 2)
                slot.width = round(room_w, 2)
                slot.height = round(room_h, 2)
                slot.placed = True

                rooms.append(PlanRoom(
                    name=slot.name, room_type=slot.room_type,
                    x=slot.x, y=slot.y,
                    width=slot.width, height=slot.height,
                    has_exterior_wall=False, facing_direction="",
                ))
                current_y += room_h
    else:
        # Tek tek yerleştir (biri yoksa)
        for slot in [banyo_slot, wc_slot]:
            if slot is None or slot.placed:
                continue
            remaining_h = zy + zh - current_y
            if remaining_h < slot.min_width:
                continue
            room_w = zw
            room_h = slot.target_area / room_w if room_w > 0 else 2.5
            room_h = max(slot.min_width, min(room_h, remaining_h))

            slot.x = round(zx, 2)
            slot.y = round(current_y, 2)
            slot.width = round(room_w, 2)
            slot.height = round(room_h, 2)
            slot.placed = True

            rooms.append(PlanRoom(
                name=slot.name, room_type=slot.room_type,
                x=slot.x, y=slot.y,
                width=slot.width, height=slot.height,
                has_exterior_wall=False, facing_direction="",
            ))
            current_y += room_h

    # Kalan ıslak hacimler (varsa) üst üste dizilir
    for slot in diger_slots:
        if slot.placed:
            continue
        remaining_h = zy + zh - current_y
        if remaining_h < slot.min_width:
            continue
        room_w = zw
        room_h = slot.target_area / room_w if room_w > 0 else 2.5
        room_h = max(slot.min_width, min(room_h, remaining_h))

        slot.x = round(zx, 2)
        slot.y = round(current_y, 2)
        slot.width = round(room_w, 2)
        slot.height = round(room_h, 2)
        slot.placed = True

        rooms.append(PlanRoom(
            name=slot.name, room_type=slot.room_type,
            x=slot.x, y=slot.y,
            width=slot.width, height=slot.height,
            has_exterior_wall=False, facing_direction="",
        ))
        current_y += room_h

    zone["remaining_area"] = max(0, zw * (zy + zh - current_y))


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
