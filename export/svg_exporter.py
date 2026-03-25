"""
SVG Dışa Aktarma — svgwrite ile vektörel plan çizimi.
"""

import math
import logging

logger = logging.getLogger(__name__)

ROOM_COLORS_SVG = {
    "salon": "#E3F2FD", "yatak_odasi": "#FFF3E0", "mutfak": "#E8F5E9",
    "banyo": "#F3E5F5", "wc": "#FCE4EC", "antre": "#FFF9C4",
    "koridor": "#F5F5F5", "balkon": "#E0F7FA", "diger": "#F5F5F5",
}


def export_svg(plan, output_path: str = "kat_plani.svg", scale: float = 40.0,
               show_dimensions: bool = True, show_furniture: bool = False) -> str:
    """Kat planını SVG formatında kaydeder.

    Args:
        plan: FloorPlan nesnesi.
        output_path: Çıktı dosya yolu.
        scale: Piksel/metre oranı.
        show_dimensions: Ölçü çizgileri göster.

    Returns:
        Dosya yolu.
    """
    try:
        import svgwrite
    except ImportError:
        logger.error("svgwrite kurulu değil. pip install svgwrite")
        return ""

    if not plan or not plan.rooms:
        return ""

    # Boyut hesapla
    max_x = max(r.x + r.width for r in plan.rooms)
    max_y = max(r.y + r.height for r in plan.rooms)
    margin = 3
    width = (max_x + margin * 2) * scale
    height = (max_y + margin * 2) * scale

    dwg = svgwrite.Drawing(output_path, size=(f"{width:.0f}px", f"{height:.0f}px"),
                           viewBox=f"0 0 {width:.0f} {height:.0f}")

    # Arka plan
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="white"))

    # Style
    dwg.defs.add(dwg.style("""
        .room-label { font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; fill: #333; text-anchor: middle; }
        .room-area { font-family: Arial, sans-serif; font-size: 10px; fill: #666; text-anchor: middle; font-style: italic; }
        .dim-text { font-family: Arial, sans-serif; font-size: 8px; fill: #999; text-anchor: middle; }
        .wall-ext { stroke: #1a1a1a; stroke-width: 3; fill: none; }
        .wall-int { stroke: #666; stroke-width: 1.5; fill: none; }
        .window { stroke: #1E88E5; stroke-width: 3; fill: none; }
        .door-arc { stroke: #E65100; stroke-width: 1; fill: none; stroke-dasharray: 4,3; }
        .hatch { fill: url(#hatch_pattern); opacity: 0.3; }
    """))

    # Islak hacim tarama deseni
    hatch = dwg.defs.add(dwg.pattern(id="hatch_pattern", size=(8, 8), patternUnits="userSpaceOnUse"))
    hatch.add(dwg.line(start=(0, 0), end=(8, 8), stroke="#9C27B0", stroke_width=0.5))

    ox = margin * scale
    oy = margin * scale

    for room in plan.rooms:
        rx = ox + room.x * scale
        ry = oy + room.y * scale
        rw = room.width * scale
        rh = room.height * scale

        color = ROOM_COLORS_SVG.get(room.room_type, "#F5F5F5")
        wall_class = "wall-ext" if room.has_exterior_wall else "wall-int"

        # Oda dolgusu
        dwg.add(dwg.rect(insert=(rx, ry), size=(rw, rh), fill=color, opacity=0.6))

        # Islak hacim tarama
        if room.room_type in ("banyo", "wc"):
            dwg.add(dwg.rect(insert=(rx, ry), size=(rw, rh), **{"class": "hatch"}))

        # Duvar çerçevesi
        dwg.add(dwg.rect(insert=(rx, ry), size=(rw, rh), **{"class": wall_class}))

        # Oda ismi
        cx, cy = rx + rw / 2, ry + rh / 2
        dwg.add(dwg.text(room.name, insert=(cx, cy - 3), **{"class": "room-label"}))
        dwg.add(dwg.text(f"{room.area:.1f} m²", insert=(cx, cy + 12), **{"class": "room-area"}))

        # Pencereler
        for window in room.windows:
            _draw_window_svg(dwg, room, window, ox, oy, scale)

        # Kapılar
        for door in room.doors:
            _draw_door_svg(dwg, room, door, ox, oy, scale)

        # Ölçüler
        if show_dimensions:
            # Genişlik (alt)
            dwg.add(dwg.line(start=(rx, ry + rh + 8), end=(rx + rw, ry + rh + 8),
                            stroke="#999", stroke_width=0.5))
            dwg.add(dwg.text(f"{room.width:.2f}", insert=(cx, ry + rh + 18), **{"class": "dim-text"}))
            # Yükseklik (sol)
            t = dwg.text(f"{room.height:.2f}", insert=(rx - 15, cy), **{"class": "dim-text"})
            t.rotate(-90, center=(rx - 15, cy))
            dwg.add(t)

    # Kuzey oku
    arrow_x = ox + max_x * scale + 1.5 * scale
    arrow_y = oy + 1 * scale
    dwg.add(dwg.line(start=(arrow_x, arrow_y + 1.5 * scale), end=(arrow_x, arrow_y),
                     stroke="red", stroke_width=2))
    dwg.add(dwg.polygon(
        points=[(arrow_x, arrow_y - 5), (arrow_x - 4, arrow_y + 5), (arrow_x + 4, arrow_y + 5)],
        fill="red",
    ))
    dwg.add(dwg.text("K", insert=(arrow_x, arrow_y - 10),
                     style="font-family:Arial;font-size:14px;font-weight:bold;fill:red;text-anchor:middle"))

    # Ölçek çubuğu
    sb_y = oy + max_y * scale + 2 * scale
    dwg.add(dwg.line(start=(ox, sb_y), end=(ox + 5 * scale, sb_y), stroke="black", stroke_width=2))
    dwg.add(dwg.text("5 m (1:100)", insert=(ox + 2.5 * scale, sb_y + 15), **{"class": "dim-text"}))

    dwg.save()
    logger.info(f"SVG kaydedildi: {output_path}")
    return output_path


def export_svg_string(plan, scale: float = 40.0,
                      show_dimensions: bool = True,
                      show_furniture: bool = False) -> str:
    """Kat planını SVG formatında string olarak döndürür.

    Args:
        plan: FloorPlan nesnesi.
        scale: Piksel/metre oranı.
        show_dimensions: Ölçü çizgileri göster.

    Returns:
        SVG içeriği (string).
    """
    try:
        import svgwrite
    except ImportError:
        logger.error("svgwrite kurulu değil. pip install svgwrite")
        return ""

    if not plan or not plan.rooms:
        return ""

    # Boyut hesapla
    max_x = max(r.x + r.width for r in plan.rooms)
    max_y = max(r.y + r.height for r in plan.rooms)
    margin = 3
    width = (max_x + margin * 2) * scale
    height = (max_y + margin * 2) * scale

    # Dosya adı yerine None vererek bellekte oluştur
    dwg = svgwrite.Drawing(size=(f"{width:.0f}px", f"{height:.0f}px"),
                           viewBox=f"0 0 {width:.0f} {height:.0f}")

    # Arka plan
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="white"))

    # Style
    dwg.defs.add(dwg.style("""
        .room-label { font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; fill: #333; text-anchor: middle; }
        .room-area { font-family: Arial, sans-serif; font-size: 10px; fill: #666; text-anchor: middle; font-style: italic; }
        .dim-text { font-family: Arial, sans-serif; font-size: 8px; fill: #999; text-anchor: middle; }
        .wall-ext { stroke: #1a1a1a; stroke-width: 3; fill: none; }
        .wall-int { stroke: #666; stroke-width: 1.5; fill: none; }
        .window { stroke: #1E88E5; stroke-width: 3; fill: none; }
        .door-arc { stroke: #E65100; stroke-width: 1; fill: none; stroke-dasharray: 4,3; }
        .hatch { fill: url(#hatch_pattern); opacity: 0.3; }
    """))

    # Islak hacim tarama deseni
    hatch = dwg.defs.add(dwg.pattern(id="hatch_pattern", size=(8, 8), patternUnits="userSpaceOnUse"))
    hatch.add(dwg.line(start=(0, 0), end=(8, 8), stroke="#9C27B0", stroke_width=0.5))

    ox = margin * scale
    oy = margin * scale

    for room in plan.rooms:
        rx = ox + room.x * scale
        ry = oy + room.y * scale
        rw = room.width * scale
        rh = room.height * scale

        color = ROOM_COLORS_SVG.get(room.room_type, "#F5F5F5")
        wall_class = "wall-ext" if room.has_exterior_wall else "wall-int"

        # Oda dolgusu
        dwg.add(dwg.rect(insert=(rx, ry), size=(rw, rh), fill=color, opacity=0.6))

        # Islak hacim tarama
        if room.room_type in ("banyo", "wc"):
            dwg.add(dwg.rect(insert=(rx, ry), size=(rw, rh), **{"class": "hatch"}))

        # Duvar çerçevesi
        dwg.add(dwg.rect(insert=(rx, ry), size=(rw, rh), **{"class": wall_class}))

        # Oda ismi
        cx, cy = rx + rw / 2, ry + rh / 2
        dwg.add(dwg.text(room.name, insert=(cx, cy - 3), **{"class": "room-label"}))
        dwg.add(dwg.text(f"{room.area:.1f} m²", insert=(cx, cy + 12), **{"class": "room-area"}))

        # Pencereler
        for window in room.windows:
            _draw_window_svg(dwg, room, window, ox, oy, scale)

        # Kapılar
        for door in room.doors:
            _draw_door_svg(dwg, room, door, ox, oy, scale)

        # Ölçüler
        if show_dimensions:
            dwg.add(dwg.line(start=(rx, ry + rh + 8), end=(rx + rw, ry + rh + 8),
                            stroke="#999", stroke_width=0.5))
            dwg.add(dwg.text(f"{room.width:.2f}", insert=(cx, ry + rh + 18), **{"class": "dim-text"}))
            t = dwg.text(f"{room.height:.2f}", insert=(rx - 15, cy), **{"class": "dim-text"})
            t.rotate(-90, center=(rx - 15, cy))
            dwg.add(t)

    # Kuzey oku
    arrow_x = ox + max_x * scale + 1.5 * scale
    arrow_y = oy + 1 * scale
    dwg.add(dwg.line(start=(arrow_x, arrow_y + 1.5 * scale), end=(arrow_x, arrow_y),
                     stroke="red", stroke_width=2))
    dwg.add(dwg.polygon(
        points=[(arrow_x, arrow_y - 5), (arrow_x - 4, arrow_y + 5), (arrow_x + 4, arrow_y + 5)],
        fill="red",
    ))
    dwg.add(dwg.text("K", insert=(arrow_x, arrow_y - 10),
                     style="font-family:Arial;font-size:14px;font-weight:bold;fill:red;text-anchor:middle"))

    # Ölçek çubuğu
    sb_y = oy + max_y * scale + 2 * scale
    dwg.add(dwg.line(start=(ox, sb_y), end=(ox + 5 * scale, sb_y), stroke="black", stroke_width=2))
    dwg.add(dwg.text("5 m (1:100)", insert=(ox + 2.5 * scale, sb_y + 15), **{"class": "dim-text"}))

    return dwg.tostring()


def export_svg_bytes(plan, scale: float = 40.0,
                     show_dimensions: bool = True,
                     show_furniture: bool = False) -> bytes:
    """Kat planını SVG formatında bytes olarak döndürür (Streamlit indirme butonu için).

    Args:
        plan: FloorPlan nesnesi.
        scale: Piksel/metre oranı.
        show_dimensions: Ölçü çizgileri göster.

    Returns:
        SVG içeriği (bytes, UTF-8 kodlamalı).
    """
    svg_str = export_svg_string(plan, scale=scale,
                                show_dimensions=show_dimensions,
                                show_furniture=show_furniture)
    return svg_str.encode("utf-8") if svg_str else b""


def _draw_window_svg(dwg, room, window, ox, oy, scale):
    w_wall = window.get("wall", "south")
    pos = window.get("position", 0.5)
    w_width = window.get("width", 1.2) * scale
    rx = ox + room.x * scale
    ry = oy + room.y * scale
    rw = room.width * scale
    rh = room.height * scale

    if w_wall == "south":
        wx = rx + rw * pos - w_width / 2
        dwg.add(dwg.line(start=(wx, ry), end=(wx + w_width, ry), **{"class": "window"}))
    elif w_wall == "north":
        wx = rx + rw * pos - w_width / 2
        dwg.add(dwg.line(start=(wx, ry + rh), end=(wx + w_width, ry + rh), **{"class": "window"}))
    elif w_wall == "east":
        wy = ry + rh * pos - w_width / 2
        dwg.add(dwg.line(start=(rx + rw, wy), end=(rx + rw, wy + w_width), **{"class": "window"}))
    elif w_wall == "west":
        wy = ry + rh * pos - w_width / 2
        dwg.add(dwg.line(start=(rx, wy), end=(rx, wy + w_width), **{"class": "window"}))


def _draw_door_svg(dwg, room, door, ox, oy, scale):
    d_wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    dw = door.get("width", 0.9) * scale
    rx = ox + room.x * scale
    ry = oy + room.y * scale
    rw = room.width * scale
    rh = room.height * scale

    if d_wall == "south":
        dx = rx + rw * pos
        path = f"M {dx},{ry} A {dw},{dw} 0 0 1 {dx + dw},{ry - dw}"
        dwg.add(dwg.path(d=path, **{"class": "door-arc"}))
    elif d_wall == "north":
        dx = rx + rw * pos
        path = f"M {dx},{ry + rh} A {dw},{dw} 0 0 0 {dx + dw},{ry + rh + dw}"
        dwg.add(dwg.path(d=path, **{"class": "door-arc"}))
