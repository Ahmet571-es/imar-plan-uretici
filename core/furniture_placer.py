"""
Otomatik Mobilya Yerleştirme — Oda boyutlarına göre uygun mobilyaları konumlandırır.

İyileştirmeler:
- Mutfak çalışma üçgeni (ocak-lavabo-buzdolabı) optimizasyonu
- Yatak başı duvara dayalı, pencere önüne konmama
- Plan renderer ile entegrasyon için render verisi
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

    def to_render_dict(self) -> dict:
        """Plan renderer için dict formatına çevirir."""
        return {
            "isim": self.isim,
            "x": self.x,
            "y": self.y,
            "en": self.en,
            "boy": self.boy,
            "rotation": self.rotation,
            "sembol": self.sembol,
        }


def place_furniture(room: PlanRoom) -> list[PlacedFurniture]:
    """Odaya uygun mobilyaları otomatik yerleştirir.

    Strateji:
    1. Duvara bitişik mobilyaları duvarlara yerleştir
    2. Yatak başı duvara dayalı, pencere önüne konmama
    3. Mutfak çalışma üçgeni optimizasyonu
    4. Serbest mobilyaları ortaya yerleştir
    5. Kapı açılma alanını ve pencere önünü boş bırak
    6. Minimum sirkülasyon boşluğunu koru
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

    # Pencere önü alanlarını occupied'a ekle (yatak odası için önemli)
    window_walls = set()
    for window in room.windows:
        wz = _get_window_zone(room, window)
        if wz:
            occupied_zones.append(wz)
            window_walls.add(window.get("wall", ""))

    # Mutfak → çalışma üçgeni optimizasyonu
    if room.room_type == "mutfak":
        placed = _place_kitchen_triangle(room, furniture_list, occupied_zones)
        return placed

    # Yatak odası → özel yerleştirme
    if room.room_type == "yatak_odasi":
        placed = _place_bedroom(room, furniture_list, occupied_zones,
                                window_walls)
        return placed

    # Diğer odalar → genel yerleştirme
    wall_cursor = {
        "south": room.x + 0.3,
        "north": room.x + 0.3,
        "west":  room.y + 0.3,
        "east":  room.y + 0.3,
    }
    wall_order = _get_wall_placement_order(room)

    for mob in furniture_list:
        if mob.get("duvar_bitisik", True):
            placed_item = _place_on_wall(room, mob, wall_cursor,
                                          wall_order, occupied_zones)
        else:
            placed_item = _place_center(room, mob, occupied_zones)

        if placed_item:
            placed.append(placed_item)
            occupied_zones.append((placed_item.x, placed_item.y,
                                   placed_item.en, placed_item.boy))

    return placed


def _place_kitchen_triangle(room: PlanRoom, furniture_list: list,
                             occupied_zones: list) -> list[PlacedFurniture]:
    """Mutfak çalışma üçgeni — ocak, lavabo, buzdolabı optimal konumda.

    İdeal üçgen kenar uzunlukları: 1.2m - 2.7m arası.
    Toplam çevre: 4.0m - 7.9m arası.
    """
    placed = []
    x, y, w, h = room.x, room.y, room.width, room.height

    # Pencereli duvara karşı duvarı bul
    window_walls = [win.get("wall", "") for win in room.windows]
    counter_wall = "north"  # Varsayılan: tezgah kuzey duvarında
    if "north" in window_walls:
        counter_wall = "south"

    # Tezgah duvarı boyunca: lavabo (merkez) — ocak (sol) — buzdolabı (sağ)
    if counter_wall == "north":
        base_y = y + h - 0.60  # Tezgah derinliği
    else:
        base_y = y

    # Lavabo — merkeze yakın
    lavabo = _find_item(furniture_list, "lavabo")
    if lavabo:
        lx = x + w * 0.45
        placed.append(PlacedFurniture(
            isim=lavabo["isim"], x=lx, y=base_y,
            en=lavabo["en"], boy=lavabo["boy"], sembol=lavabo.get("sembol", ""),
        ))

    # Ocak — lavabonun solunda
    ocak = _find_item(furniture_list, "ocak")
    if ocak:
        ox_pos = x + w * 0.20
        placed.append(PlacedFurniture(
            isim=ocak["isim"], x=ox_pos, y=base_y,
            en=ocak["en"], boy=ocak["boy"], sembol=ocak.get("sembol", ""),
        ))

    # Buzdolabı — köşede (üçgenin en uzak noktası)
    buzdolabi = _find_item(furniture_list, "buzdolabi")
    if buzdolabi:
        bx = x + w - buzdolabi["en"] - 0.1
        by = base_y if counter_wall == "north" else y + h - buzdolabi["boy"]
        placed.append(PlacedFurniture(
            isim=buzdolabi["isim"], x=bx, y=by,
            en=buzdolabi["en"], boy=buzdolabi["boy"],
            sembol=buzdolabi.get("sembol", ""),
        ))

    # Tezgah
    tezgah = _find_item(furniture_list, "tezgah")
    if tezgah:
        placed.append(PlacedFurniture(
            isim=tezgah["isim"], x=x + 0.1, y=base_y,
            en=min(tezgah["en"], w - 0.2), boy=tezgah["boy"],
            sembol=tezgah.get("sembol", ""),
        ))

    # Kalan mobilyaları normal yerleştir
    placed_names = {p.isim for p in placed}
    remaining = [m for m in furniture_list if m["isim"] not in placed_names]
    occ = [(p.x, p.y, p.en, p.boy) for p in placed] + occupied_zones
    for mob in remaining:
        item = _place_center(room, mob, occ)
        if item:
            placed.append(item)
            occ.append((item.x, item.y, item.en, item.boy))

    return placed


def _place_bedroom(room: PlanRoom, furniture_list: list,
                    occupied_zones: list,
                    window_walls: set) -> list[PlacedFurniture]:
    """Yatak odası — yatak başı duvara dayalı, pencere önüne konmaz."""
    placed = []
    x, y, w, h = room.x, room.y, room.width, room.height

    # Yatak başı için en iyi duvar: pencereli olmayan, en uzun duvar
    best_wall = None
    wall_lengths = {
        "south": w, "north": w, "west": h, "east": h
    }
    # Pencereli duvarları çıkar
    valid_walls = {k: v for k, v in wall_lengths.items()
                   if k not in window_walls}
    if not valid_walls:
        valid_walls = wall_lengths

    best_wall = max(valid_walls, key=valid_walls.get)

    # Yatağı yerleştir
    yatak = _find_item(furniture_list, "yatak")
    if yatak:
        if best_wall == "north":
            yx = x + (w - yatak["en"]) / 2
            yy = y + h - yatak["boy"]
        elif best_wall == "south":
            yx = x + (w - yatak["en"]) / 2
            yy = y
        elif best_wall == "west":
            yx = x
            yy = y + (h - yatak["en"]) / 2
            yatak["en"], yatak["boy"] = yatak["boy"], yatak["en"]
        else:  # east
            yx = x + w - yatak["boy"]
            yy = y + (h - yatak["en"]) / 2
            yatak["en"], yatak["boy"] = yatak["boy"], yatak["en"]

        placed.append(PlacedFurniture(
            isim=yatak["isim"], x=yx, y=yy,
            en=yatak["en"], boy=yatak["boy"],
            sembol=yatak.get("sembol", ""),
        ))
        occupied_zones.append((yx, yy, yatak["en"], yatak["boy"]))

    # Kalan mobilyalar
    placed_names = {p.isim for p in placed}
    remaining = [m for m in furniture_list if m["isim"] not in placed_names]
    wall_cursor = {
        "south": x + 0.3, "north": x + 0.3,
        "west": y + 0.3, "east": y + 0.3,
    }
    wall_order = _get_wall_placement_order(room)
    occ = occupied_zones

    for mob in remaining:
        if mob.get("duvar_bitisik", True):
            item = _place_on_wall(room, mob, wall_cursor, wall_order, occ)
        else:
            item = _place_center(room, mob, occ)
        if item:
            placed.append(item)
            occ.append((item.x, item.y, item.en, item.boy))

    return placed


def _find_item(furniture_list: list, keyword: str) -> dict | None:
    """Mobilya listesinden keyword içeren öğeyi bul."""
    for mob in furniture_list:
        if keyword.lower() in mob.get("isim", "").lower():
            return dict(mob)  # Copy
        if keyword.lower() in mob.get("sembol", "").lower():
            return dict(mob)
    return None


def _get_wall_placement_order(room: PlanRoom) -> list[str]:
    """Mobilya yerleştirme için duvar öncelik sırası."""
    walls = ["south", "west", "east", "north"]
    window_walls = [w.get("wall", "") for w in room.windows]
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
                    en=mob_en, boy=mob_boy, sembol=mob.get("sembol", ""),
                )
        else:
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
            en=mob["en"], boy=mob["boy"], sembol=mob.get("sembol", ""),
        )
    return None


def _overlaps_any(x, y, w, h, occupied_zones) -> bool:
    """Çakışma kontrolü."""
    margin = MIN_SIRKULASYON_BOSLUGU
    for (ox, oy, ow, oh) in occupied_zones:
        if (x < ox + ow + margin and x + w + margin > ox and
                y < oy + oh + margin and y + h + margin > oy):
            return True
    return False


def _get_door_zone(room, door) -> tuple | None:
    """Kapı açılma alanı."""
    wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    dw = door.get("width", 0.90)
    if wall == "south":
        return (room.x + room.width * pos - dw / 2, room.y, dw, dw)
    elif wall == "north":
        return (room.x + room.width * pos - dw / 2,
                room.y + room.height - dw, dw, dw)
    elif wall == "west":
        return (room.x, room.y + room.height * pos - dw / 2, dw, dw)
    elif wall == "east":
        return (room.x + room.width - dw,
                room.y + room.height * pos - dw / 2, dw, dw)
    return None


def _get_window_zone(room, window) -> tuple | None:
    """Pencere önü alanı (mobilya konmamalı)."""
    wall = window.get("wall", "south")
    pos = window.get("position", 0.5)
    ww = window.get("width", 1.20)
    depth = 0.60  # Pencere önü boş alan derinliği

    if wall == "south":
        wx = room.x + room.width * pos - ww / 2
        return (wx, room.y, ww, depth)
    elif wall == "north":
        wx = room.x + room.width * pos - ww / 2
        return (wx, room.y + room.height - depth, ww, depth)
    elif wall == "west":
        wy = room.y + room.height * pos - ww / 2
        return (room.x, wy, depth, ww)
    elif wall == "east":
        wy = room.y + room.height * pos - ww / 2
        return (room.x + room.width - depth, wy, depth, ww)
    return None


def place_all_rooms(rooms: list[PlanRoom]) -> list[dict]:
    """Tüm odalar için mobilya yerleştirip render verisi döndürür."""
    all_furniture = []
    for room in rooms:
        placed = place_furniture(room)
        for p in placed:
            all_furniture.append(p.to_render_dict())
    return all_furniture


# ══════════════════════════════════════════════════════════════
# DERİNLEŞTİRİLMİŞ YERLEŞTİRME FONKSİYONLARI
# ══════════════════════════════════════════════════════════════

def evaluate_furniture_placement(room: PlanRoom, placed: list[PlacedFurniture]) -> dict:
    """Mobilya yerleştirme kalitesini değerlendirir.

    Returns:
        {
            "puan": int (0-100),
            "toplam_mobilya_alani": float,
            "doluluk_orani": float,
            "sirkulasyon_yeterli": bool,
            "ergonomi_sorunlari": list[str],
            "oneriler": list[str],
        }
    """
    if not placed or room.area <= 0:
        return {"puan": 0, "toplam_mobilya_alani": 0, "doluluk_orani": 0,
                "sirkulasyon_yeterli": True, "ergonomi_sorunlari": [], "oneriler": []}

    toplam_mob_alan = sum(p.en * p.boy for p in placed)
    doluluk = toplam_mob_alan / room.area
    sorunlar = []
    oneriler = []
    puan = 100

    # Doluluk oranı kontrolü
    if doluluk > 0.60:
        puan -= 20
        sorunlar.append(f"Oda çok dolu: %{doluluk*100:.0f} (max %60 önerilir)")
        oneriler.append("Daha kompakt mobilya seçimi yapın veya mobilya azaltın")
    elif doluluk < 0.15:
        puan -= 10
        oneriler.append("Oda çok boş — ek mobilya eklenebilir")

    # Sirkülasyon boşluğu kontrolü
    sirk_yeterli = True
    for i, p1 in enumerate(placed):
        for p2 in placed[i+1:]:
            gap_x = abs((p1.x + p1.en) - p2.x)
            gap_y = abs((p1.y + p1.boy) - p2.y)
            min_gap = min(gap_x, gap_y)
            if min_gap < MIN_SIRKULASYON_BOSLUGU and min_gap > 0:
                sirk_yeterli = False
                sorunlar.append(f"{p1.isim} ↔ {p2.isim} arası boşluk yetersiz ({min_gap:.2f}m < {MIN_SIRKULASYON_BOSLUGU}m)")
                puan -= 10

    # Pencere önü kontrolü
    for p in placed:
        for win in room.windows:
            wz = _get_window_zone(room, win)
            if wz and _overlaps_any(p.x, p.y, p.en, p.boy, [wz]):
                sorunlar.append(f"{p.isim} pencere önünü kapatıyor")
                puan -= 5

    # Kapı açılma kontrolü
    for p in placed:
        for door in room.doors:
            dz = _get_door_zone(room, door)
            if dz and _overlaps_any(p.x, p.y, p.en, p.boy, [dz]):
                sorunlar.append(f"{p.isim} kapı açılma alanını engelliyor")
                puan -= 10

    # Oda tipine özel kontroller
    if room.room_type == "salon":
        # TV-koltuk mesafesi kontrolü (ideal: 2.5-4.0m)
        tv = next((p for p in placed if "tv" in p.isim.lower()), None)
        koltuk = next((p for p in placed if "koltuk" in p.isim.lower()), None)
        if tv and koltuk:
            dist = math.sqrt((tv.x - koltuk.x)**2 + (tv.y - koltuk.y)**2)
            if dist < 2.0:
                sorunlar.append(f"TV-koltuk mesafesi çok yakın: {dist:.1f}m (min 2.5m)")
                puan -= 5
            elif dist > 5.0:
                sorunlar.append(f"TV-koltuk mesafesi çok uzak: {dist:.1f}m (max 4.0m)")
                puan -= 5

    elif room.room_type == "mutfak":
        # Mutfak çalışma üçgeni kontrolü
        ocak = next((p for p in placed if "ocak" in p.isim.lower()), None)
        lavabo = next((p for p in placed if "lavabo" in p.isim.lower()), None)
        buzdolabi = next((p for p in placed if "buzdolabı" in p.isim.lower() or "buzdolabi" in p.sembol.lower()), None)
        if ocak and lavabo and buzdolabi:
            d1 = math.sqrt((ocak.x - lavabo.x)**2 + (ocak.y - lavabo.y)**2)
            d2 = math.sqrt((lavabo.x - buzdolabi.x)**2 + (lavabo.y - buzdolabi.y)**2)
            d3 = math.sqrt((ocak.x - buzdolabi.x)**2 + (ocak.y - buzdolabi.y)**2)
            cevre = d1 + d2 + d3
            if cevre < 4.0:
                sorunlar.append(f"Mutfak üçgeni çok dar: {cevre:.1f}m (min 4.0m)")
                puan -= 5
            elif cevre > 7.9:
                sorunlar.append(f"Mutfak üçgeni çok geniş: {cevre:.1f}m (max 7.9m)")
                puan -= 5

    return {
        "puan": max(0, min(100, puan)),
        "toplam_mobilya_alani": round(toplam_mob_alan, 1),
        "doluluk_orani": round(doluluk, 2),
        "sirkulasyon_yeterli": sirk_yeterli,
        "ergonomi_sorunlari": sorunlar,
        "oneriler": oneriler,
    }
