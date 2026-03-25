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
