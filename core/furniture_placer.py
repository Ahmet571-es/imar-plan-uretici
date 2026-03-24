"""
Otomatik Mobilya Yerleştirme — Oda boyutlarına göre uygun mobilyaları konumlandırır.
"""

import math
from dataclasses import dataclass, field
from core.plan_scorer import PlanRoom
from config.furniture_library import (
    get_furniture_for_room,
    select_furniture_by_area,
    MIN_SIRKULASYON_BOSLUGU,
)


@dataclass
class PlacedFurniture:
    """Yerleştirilmiş mobilya."""
    isim: str
    x: float
    y: float
    en: float
    boy: float
    rotation: float = 0  # derece
    sembol: str = ""


def place_furniture(room: PlanRoom) -> list[PlacedFurniture]:
    """Odaya uygun mobilyaları otomatik yerleştirir.

    Strateji:
    1. Duvara bitişik mobilyaları duvarlara yerleştir
    2. Serbest mobilyaları ortaya yerleştir
    3. Kapı açılma alanını ve pencere önünü boş bırak
    4. Minimum sirkülasyon boşluğunu koru
    """
    furniture_list = select_furniture_by_area(room.room_type, room.area)
    if not furniture_list:
        return []

    placed = []
    occupied_zones = []

    # Kapı açılma alanlarını occupied'a ekle
    for door in room.doors:
        dz = _get_door_zone(room, door)
        if dz:
            occupied_zones.append(dz)

    # Duvara bitişik mobilyaları yerleştir
    wall_cursor = {
        "south": room.x + 0.3,  # Alt duvar
        "north": room.x + 0.3,  # Üst duvar
        "west":  room.y + 0.3,  # Sol duvar
        "east":  room.y + 0.3,  # Sağ duvar
    }

    wall_order = _get_wall_placement_order(room)

    for mob in furniture_list:
        if mob.get("duvar_bitisik", True):
            placed_item = _place_on_wall(room, mob, wall_cursor, wall_order, occupied_zones)
        else:
            placed_item = _place_center(room, mob, occupied_zones)

        if placed_item:
            placed.append(placed_item)
            occupied_zones.append((placed_item.x, placed_item.y,
                                   placed_item.en, placed_item.boy))

    return placed


def _get_wall_placement_order(room: PlanRoom) -> list[str]:
    """Mobilya yerleştirme için duvar öncelik sırası."""
    # Pencereli duvardan kaçın (yüksek mobilya için)
    walls = ["south", "west", "east", "north"]
    window_walls = [w.get("wall", "") for w in room.windows]
    # Pencereli duvarları sona at
    for ww in window_walls:
        if ww in walls:
            walls.remove(ww)
            walls.append(ww)
    return walls


def _place_on_wall(room, mob, wall_cursor, wall_order, occupied):
    """Mobilyayı duvara bitişik yerleştir."""
    mob_en = mob["en"]
    mob_boy = mob["boy"]

    for wall in wall_order:
        if wall in ("south", "north"):
            # Yatay duvar
            cursor = wall_cursor.get(wall, room.x)
            if cursor + mob_en > room.x + room.width - 0.1:
                continue

            if wall == "south":
                fx, fy = cursor, room.y
            else:
                fx, fy = cursor, room.y + room.height - mob_boy

            if not _overlaps_any(fx, fy, mob_en, mob_boy, occupied):
                wall_cursor[wall] = cursor + mob_en + 0.1
                return PlacedFurniture(
                    isim=mob["isim"], x=fx, y=fy,
                    en=mob_en, boy=mob_boy,
                    sembol=mob.get("sembol", ""),
                )

        else:
            # Dikey duvar — mobilyayı döndür
            cursor = wall_cursor.get(wall, room.y)
            if cursor + mob_en > room.y + room.height - 0.1:
                continue

            if wall == "west":
                fx, fy = room.x, cursor
            else:
                fx, fy = room.x + room.width - mob_boy, cursor

            if not _overlaps_any(fx, fy, mob_boy, mob_en, occupied):
                wall_cursor[wall] = cursor + mob_en + 0.1
                return PlacedFurniture(
                    isim=mob["isim"], x=fx, y=fy,
                    en=mob_boy, boy=mob_en, rotation=90,
                    sembol=mob.get("sembol", ""),
                )

    return None


def _place_center(room, mob, occupied):
    """Mobilyayı oda merkezine yakın yerleştir."""
    cx = room.x + (room.width - mob["en"]) / 2
    cy = room.y + (room.height - mob["boy"]) / 2

    if not _overlaps_any(cx, cy, mob["en"], mob["boy"], occupied):
        return PlacedFurniture(
            isim=mob["isim"], x=cx, y=cy,
            en=mob["en"], boy=mob["boy"],
            sembol=mob.get("sembol", ""),
        )
    return None


def _overlaps_any(x, y, w, h, occupied_zones) -> bool:
    """Verilen dikdörtgenin mevcut zonlarla çakışıp çakışmadığını kontrol eder."""
    margin = MIN_SIRKULASYON_BOSLUGU
    for (ox, oy, ow, oh) in occupied_zones:
        if (x < ox + ow + margin and x + w + margin > ox and
            y < oy + oh + margin and y + h + margin > oy):
            return True
    return False


def _get_door_zone(room, door) -> tuple | None:
    """Kapı açılma alanını hesapla."""
    wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    dw = door.get("width", 0.90)

    if wall == "south":
        return (room.x + room.width * pos - dw/2, room.y, dw, dw)
    elif wall == "north":
        return (room.x + room.width * pos - dw/2, room.y + room.height - dw, dw, dw)
    elif wall == "west":
        return (room.x, room.y + room.height * pos - dw/2, dw, dw)
    elif wall == "east":
        return (room.x + room.width - dw, room.y + room.height * pos - dw/2, dw, dw)
    return None
