"""
DXF (AutoCAD) Dışa Aktarma — ezdxf ile katmanlı mimari çizim.
"""

import logging
import math

logger = logging.getLogger(__name__)


def export_dxf(plan, output_path: str = "kat_plani.dxf", scale: float = 1.0) -> str:
    """Kat planını DXF formatında kaydeder.

    Args:
        plan: FloorPlan nesnesi (rooms listesi).
        output_path: Çıktı dosya yolu.
        scale: Ölçek çarpanı.

    Returns:
        Dosya yolu veya boş string.
    """
    try:
        import ezdxf
        from ezdxf.enums import TextEntityAlignment
    except ImportError:
        logger.error("ezdxf kurulu değil. pip install ezdxf")
        return ""

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # ── Katmanlar ──
    doc.layers.add("DUVAR_DIS", color=7, lineweight=50)       # Beyaz, kalın
    doc.layers.add("DUVAR_IC", color=8, lineweight=25)         # Gri
    doc.layers.add("KAPI", color=1, lineweight=15)             # Kırmızı
    doc.layers.add("PENCERE", color=5, lineweight=15)          # Mavi
    doc.layers.add("OLCU", color=3, lineweight=5)              # Yeşil
    doc.layers.add("METIN", color=2, lineweight=5)             # Sarı
    doc.layers.add("MOBILYA", color=8, lineweight=5)           # Gri
    doc.layers.add("HATCH", color=6)                           # Magenta

    if not plan or not plan.rooms:
        doc.saveas(output_path)
        return output_path

    for room in plan.rooms:
        x, y = room.x * scale, room.y * scale
        w, h = room.width * scale, room.height * scale
        layer = "DUVAR_DIS" if room.has_exterior_wall else "DUVAR_IC"

        # ── Duvarlar (dikdörtgen) ──
        points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        msp.add_lwpolyline(points, dxfattribs={"layer": layer})

        # ── Oda ismi ──
        cx, cy = x + w / 2, y + h / 2
        msp.add_text(
            room.name,
            dxfattribs={
                "layer": "METIN",
                "height": 0.25 * scale,
                "insert": (cx, cy + 0.2 * scale),
            },
        ).set_placement((cx, cy + 0.2 * scale), align=TextEntityAlignment.MIDDLE_CENTER)

        # ── Alan ──
        msp.add_text(
            f"{room.area:.1f} m²",
            dxfattribs={
                "layer": "METIN",
                "height": 0.18 * scale,
                "insert": (cx, cy - 0.3 * scale),
            },
        ).set_placement((cx, cy - 0.3 * scale), align=TextEntityAlignment.MIDDLE_CENTER)

        # ── Ölçü çizgileri ──
        # Alt kenar (genişlik)
        _add_dimension(msp, (x, y - 0.4 * scale), (x + w, y - 0.4 * scale),
                       f"{room.width:.2f}", scale)
        # Sol kenar (yükseklik)
        _add_dimension(msp, (x - 0.4 * scale, y), (x - 0.4 * scale, y + h),
                       f"{room.height:.2f}", scale, vertical=True)

        # ── Pencereler ──
        for window in room.windows:
            _draw_window_dxf(msp, room, window, scale)

        # ── Kapılar ──
        for door in room.doors:
            _draw_door_dxf(msp, room, door, scale)

        # ── Islak hacim taraması ──
        if room.room_type in ("banyo", "wc"):
            hatch = msp.add_hatch(color=6, dxfattribs={"layer": "HATCH"})
            hatch.paths.add_polyline_path(
                [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                is_closed=True,
            )
            hatch.set_pattern_fill("ANSI31", scale=0.5 * scale)

    # ── Kuzey oku ──
    max_x = max(r.x + r.width for r in plan.rooms) * scale + 2 * scale
    max_y = max(r.y + r.height for r in plan.rooms) * scale
    msp.add_line((max_x, max_y - 1.5 * scale), (max_x, max_y), dxfattribs={"layer": "OLCU"})
    msp.add_text("K", dxfattribs={
        "layer": "METIN", "height": 0.4 * scale,
        "insert": (max_x - 0.15 * scale, max_y + 0.2 * scale),
    })

    # ── Ölçek çubuğu ──
    msp.add_line((0, -1.5 * scale), (5 * scale, -1.5 * scale), dxfattribs={"layer": "OLCU"})
    msp.add_text(f"5 m (1:{int(100/scale)})", dxfattribs={
        "layer": "METIN", "height": 0.2 * scale,
        "insert": (2.5 * scale, -1.8 * scale),
    })

    doc.saveas(output_path)
    logger.info(f"DXF kaydedildi: {output_path}")
    return output_path


def _add_dimension(msp, p1, p2, text, scale, vertical=False):
    """Basit ölçü çizgisi ekler."""
    msp.add_line(p1, p2, dxfattribs={"layer": "OLCU"})
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    offset = -0.25 * scale if not vertical else 0
    msp.add_text(text, dxfattribs={
        "layer": "OLCU", "height": 0.15 * scale,
        "insert": (mid[0] + offset, mid[1] - 0.15 * scale),
    })


def _draw_window_dxf(msp, room, window, scale):
    """DXF'te pencere çizer."""
    wall = window.get("wall", "south")
    pos = window.get("position", 0.5)
    w_width = window.get("width", 1.2) * scale
    x, y = room.x * scale, room.y * scale
    rw, rh = room.width * scale, room.height * scale
    gap = 0.06 * scale

    if wall == "south":
        wx = x + rw * pos - w_width / 2
        msp.add_line((wx, y), (wx + w_width, y), dxfattribs={"layer": "PENCERE"})
        msp.add_line((wx, y - gap), (wx + w_width, y - gap), dxfattribs={"layer": "PENCERE"})
    elif wall == "north":
        wx = x + rw * pos - w_width / 2
        msp.add_line((wx, y + rh), (wx + w_width, y + rh), dxfattribs={"layer": "PENCERE"})
        msp.add_line((wx, y + rh + gap), (wx + w_width, y + rh + gap), dxfattribs={"layer": "PENCERE"})
    elif wall == "east":
        wy = y + rh * pos - w_width / 2
        msp.add_line((x + rw, wy), (x + rw, wy + w_width), dxfattribs={"layer": "PENCERE"})
        msp.add_line((x + rw + gap, wy), (x + rw + gap, wy + w_width), dxfattribs={"layer": "PENCERE"})
    elif wall == "west":
        wy = y + rh * pos - w_width / 2
        msp.add_line((x, wy), (x, wy + w_width), dxfattribs={"layer": "PENCERE"})
        msp.add_line((x - gap, wy), (x - gap, wy + w_width), dxfattribs={"layer": "PENCERE"})


def _draw_door_dxf(msp, room, door, scale):
    """DXF'te kapı yayı çizer."""
    wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    dw = door.get("width", 0.9) * scale
    x, y = room.x * scale, room.y * scale
    rw, rh = room.width * scale, room.height * scale

    if wall == "south":
        dx = x + rw * pos
        msp.add_arc(center=(dx, y), radius=dw, start_angle=0, end_angle=90,
                    dxfattribs={"layer": "KAPI"})
    elif wall == "north":
        dx = x + rw * pos
        msp.add_arc(center=(dx, y + rh), radius=dw, start_angle=270, end_angle=360,
                    dxfattribs={"layer": "KAPI"})
    elif wall == "east":
        dy = y + rh * pos
        msp.add_arc(center=(x + rw, dy), radius=dw, start_angle=90, end_angle=180,
                    dxfattribs={"layer": "KAPI"})
    elif wall == "west":
        dy = y + rh * pos
        msp.add_arc(center=(x, dy), radius=dw, start_angle=0, end_angle=90,
                    dxfattribs={"layer": "KAPI"})
