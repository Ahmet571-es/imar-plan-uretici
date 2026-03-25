"""
Plan finalizasyonu — kapı ve pencere ekleme, dış duvar tespiti.
"""

from core.plan_scorer import PlanRoom


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
