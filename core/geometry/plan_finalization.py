"""
Plan finalizasyonu — kapı ve pencere ekleme, dış duvar tespiti, kapı açılım yönü kontrolü.
"""

import logging
from core.plan_scorer import PlanRoom

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# KAPI AÇILIM YÖNÜ YARDIMCILARI
# ═══════════════════════════════════════════════════════════════

def _determine_door_swing(room: PlanRoom, door: dict, all_rooms: list[PlanRoom]) -> str:
    """Kapının açılım yönünü belirler (inward / outward).

    Kurallar:
    - Islak hacimler (banyo, wc): kapı dışa (outward) açılır (güvenlik)
    - Yatak odası, salon: kapı içe (inward) açılır
    - Koridor kapıları: koridor tarafına (outward) açılır
    - Küçük odalar (< 5m²): kapı dışa açılır (iç alan kazanımı)

    Returns:
        "inward" veya "outward"
    """
    # Islak hacimler güvenlik gereği dışa açılır
    if room.room_type in ("banyo", "wc"):
        return "outward"

    # Küçük odalar — kapı dışa açılır, iç alan kazanımı için
    if room.area < 5.0:
        return "outward"

    # Varsayılan: içe açılır
    return "inward"


def _check_door_swing_collision(room: PlanRoom, door: dict, swing: str,
                                 all_rooms: list[PlanRoom]) -> bool:
    """Kapı açılımının başka kapıya çarpıp çarpmadığını kontrol eder.

    Kapının açıldığı alandaki kapı genişliği kadar yarıçaplı bölgede
    başka kapı olup olmadığını kontrol eder.

    Returns:
        True ise çarpışma var.
    """
    door_width = door.get("width", 0.90)
    wall = door.get("wall", "north")
    position = door.get("position", 0.5)

    # Kapının dünya koordinatlarını hesapla
    if wall == "north":
        door_x = room.x + room.width * position
        door_y = room.y + room.height
    elif wall == "south":
        door_x = room.x + room.width * position
        door_y = room.y
    elif wall == "east":
        door_x = room.x + room.width
        door_y = room.y + room.height * position
    else:  # west
        door_x = room.x
        door_y = room.y + room.height * position

    # Açılım alanı yarıçapı (kapı genişliği kadar)
    sweep_radius = door_width

    # Diğer odalardaki kapılarla çarpışma kontrolü
    for other_room in all_rooms:
        if other_room is room:
            continue
        for other_door in other_room.doors:
            other_wall = other_door.get("wall", "north")
            other_pos = other_door.get("position", 0.5)

            # Diğer kapının dünya koordinatları
            if other_wall == "north":
                od_x = other_room.x + other_room.width * other_pos
                od_y = other_room.y + other_room.height
            elif other_wall == "south":
                od_x = other_room.x + other_room.width * other_pos
                od_y = other_room.y
            elif other_wall == "east":
                od_x = other_room.x + other_room.width
                od_y = other_room.y + other_room.height * other_pos
            else:
                od_x = other_room.x
                od_y = other_room.y + other_room.height * other_pos

            # Mesafe kontrolü — kapılar arası mesafe açılım yarıçapından küçükse çarpışma
            dist = ((door_x - od_x) ** 2 + (door_y - od_y) ** 2) ** 0.5
            if dist < sweep_radius:
                return True

    return False


# ═══════════════════════════════════════════════════════════════
# KAPI VE PENCERE EKLEME
# ═══════════════════════════════════════════════════════════════

def _convert_to_plan_rooms(rooms, bw, bh, ox, oy, sun_dir, entrance_side,
                            en_suite=False):
    """Oda listesini son hale getirir — kapı ve pencere ekler.

    Kapılara door_swing alanı eklenir: "inward" veya "outward".
    Kapı açılım çarpışması tespit edilirse yön tersine çevrilir.
    """
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
        # Pencere gerektirmeyen oda tipleri
        pencere_haric = ("koridor", "antre")
        # Banyo/WC için küçük pencere (isteğe bağlı)
        kucuk_pencere_odalari = ("banyo", "wc")

        if r.room_type not in pencere_haric:
            if r.has_exterior_wall:
                # Dış duvara sahip odalar — dış duvara pencere ekle
                if is_bottom:
                    r.windows.append({"wall": "south", "position": 0.5,
                                      "width": min(1.6, r.width * 0.4)})
                if is_top:
                    r.windows.append({"wall": "north", "position": 0.5,
                                      "width": min(1.6, r.width * 0.4)})
                if is_left:
                    r.windows.append({"wall": "west", "position": 0.5,
                                      "width": min(1.4, r.height * 0.35)})
                if is_right:
                    r.windows.append({"wall": "east", "position": 0.5,
                                      "width": min(1.4, r.height * 0.35)})

                # Banyo/WC → küçük pencere (0.6m)
                if r.room_type in kucuk_pencere_odalari:
                    for win in r.windows:
                        win["width"] = 0.6

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
                if r.room_type in ("salon", "yatak_odasi"):
                    ext_walls = []
                    if is_left:
                        ext_walls.append("west")
                    if is_right:
                        ext_walls.append("east")
                    if is_bottom:
                        ext_walls.append("south")
                    if is_top:
                        ext_walls.append("north")
                    # Zaten eklenen duvarları tekrar ekleme
                    mevcut_duvarlar = {w["wall"] for w in r.windows}
                    for ew in ext_walls:
                        if ew not in mevcut_duvarlar:
                            dim = r.height if ew in ("west", "east") else r.width
                            r.windows.append({"wall": ew, "position": 0.5,
                                              "width": min(1.2, dim * 0.3)})

            else:
                # Dış duvarı olmayan oda — WC hariç pencere gerekli
                if r.room_type == "wc":
                    pass  # WC pencere almayabilir
                else:
                    # Bina merkezine göre en yakın dış kenarı bul
                    dist_left = r.x - ox
                    dist_right = (ox + bw) - (r.x + r.width)
                    dist_bottom = r.y - oy
                    dist_top = (oy + bh) - (r.y + r.height)

                    mesafeler = {
                        "west": dist_left,
                        "east": dist_right,
                        "south": dist_bottom,
                        "north": dist_top,
                    }
                    # En yakın dış kenara bakan duvar
                    en_yakin = min(mesafeler, key=mesafeler.get)

                    if en_yakin in ("west", "east"):
                        w_size = min(1.2, r.height * 0.3)
                    else:
                        w_size = min(1.2, r.width * 0.3)

                    # Banyo → küçük pencere
                    if r.room_type in kucuk_pencere_odalari:
                        w_size = 0.6

                    r.windows.append({"wall": en_yakin, "position": 0.5,
                                      "width": w_size})

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

    # ── Kapı açılım yönü ataması ve çarpışma kontrolü ──
    for r in result:
        for door in r.doors:
            swing = _determine_door_swing(r, door, result)

            # Çarpışma kontrolü — çarpışma varsa yönü tersine çevir
            if _check_door_swing_collision(r, door, swing, result):
                swing = "outward" if swing == "inward" else "inward"
                logger.debug(
                    "Kapı açılım çarpışması: %s kapısı %s olarak değiştirildi",
                    r.name, swing
                )

            door["door_swing"] = swing

    return result
