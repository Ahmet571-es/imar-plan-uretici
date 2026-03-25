"""
Kat Planı Matplotlib Çizimi — 2D plan görselleştirme.

İyileştirmeler:
- Duvar kalınlığı gerçekçi gösterim (dış=25cm, iç=10cm)
- Merdiven sembolü (basamak çizgileri)
- Mutfak tezgah sembolü
- Islak hacim taraması (hatch)
- Ölçü çizgileri üst üste binmesini önleme
- Mobilya render desteği
"""

import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc, FancyArrowPatch, Rectangle
from core.plan_scorer import FloorPlan, PlanRoom
from utils.constants import (
    DIS_DUVAR_KALINLIK, IC_BOLME_DUVAR_KALINLIK,
    IC_TASIYICI_DUVAR_KALINLIK,
)

# Oda tipi renk paleti
ROOM_COLORS = {
    "salon":       "#E3F2FD",
    "yatak_odasi": "#FFF3E0",
    "mutfak":      "#E8F5E9",
    "banyo":       "#E1D5F0",
    "wc":          "#F8D7E0",
    "antre":       "#FFF9C4",
    "koridor":     "#F5F5F5",
    "balkon":      "#E0F7FA",
    "depo":        "#EFEBE9",
    "merdiven":    "#D7CCC8",
    "salon_mutfak": "#E3F2FD",
    "diger":       "#F5F5F5",
}

ROOM_HATCH = {
    "banyo": "//",
    "wc":    "//",
}

WET_HATCH_COLOR = "#9C27B0"


def render_floor_plan(
    plan: FloorPlan,
    title: str = "Kat Planı",
    show_dimensions: bool = True,
    show_doors: bool = True,
    show_windows: bool = True,
    show_furniture: bool = False,
    show_wall_thickness: bool = True,
    furniture_data: list = None,
    figsize: tuple = (14, 11),
    scale: str = "1:100",
) -> plt.Figure:
    """Kat planını matplotlib ile çizer."""
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    if not plan.rooms:
        ax.text(0.5, 0.5, "Plan verisi yok", transform=ax.transAxes,
                ha="center", va="center", fontsize=16, color="#999")
        return fig

    dim_offset_tracker = {}

    for room in plan.rooms:
        color = ROOM_COLORS.get(room.room_type, "#F5F5F5")

        # Oda dolgu
        rect = mpatches.Rectangle(
            (room.x, room.y), room.width, room.height,
            linewidth=0, edgecolor="none", facecolor=color,
            alpha=0.7, zorder=1,
        )
        ax.add_patch(rect)

        # Islak hacim taraması
        if room.room_type in ("banyo", "wc"):
            hatch_rect = mpatches.Rectangle(
                (room.x, room.y), room.width, room.height,
                linewidth=0, edgecolor=WET_HATCH_COLOR,
                facecolor="none", hatch="///", alpha=0.3, zorder=2,
            )
            ax.add_patch(hatch_rect)

        # Duvar kalınlığı çizimi
        if show_wall_thickness:
            _draw_thick_walls(ax, room, plan)
        else:
            rect_border = mpatches.Rectangle(
                (room.x, room.y), room.width, room.height,
                linewidth=1.5 if room.has_exterior_wall else 0.8,
                edgecolor="#333" if room.has_exterior_wall else "#666",
                facecolor="none", zorder=3,
            )
            ax.add_patch(rect_border)

        # Oda ismi ve alan
        cx, cy = room.center
        ax.text(cx, cy + 0.15, room.name, ha="center", va="center",
                fontsize=8, fontweight="bold", color="#333", zorder=10)
        ax.text(cx, cy - 0.35, f"{room.area:.1f} m²",
                ha="center", va="center",
                fontsize=7, color="#666", style="italic", zorder=10)

        # Pencere/zemin oranı — penceresi olan odalar için göster
        if room.windows and room.area > 0:
            from utils.constants import PENCERE_YUKSEKLIK
            toplam_pencere_alan = sum(
                w.get("width", 1.2) * PENCERE_YUKSEKLIK
                for w in room.windows
            )
            oran = toplam_pencere_alan / room.area
            ax.text(cx, cy - 0.70,
                    f"P/Z: %{oran * 100:.0f}",
                    ha="center", va="center",
                    fontsize=5.5, color="#1565C0", zorder=10)

        # Ölçü çizgileri
        if show_dimensions:
            _draw_dimensions_smart(ax, room, dim_offset_tracker)

        # Kapılar
        if show_doors and room.doors:
            for door in room.doors:
                _draw_door(ax, room, door)

        # Pencereler
        if show_windows and room.windows:
            for window in room.windows:
                _draw_window(ax, room, window)

        # Mutfak tezgah sembolü
        if room.room_type in ("mutfak", "salon_mutfak"):
            _draw_kitchen_counter(ax, room)

        # Merdiven sembolü
        if room.room_type == "merdiven":
            _draw_staircase(ax, room)

    # Mobilya render
    if show_furniture and furniture_data:
        for furn in furniture_data:
            _draw_furniture_item(ax, furn)

    # Kuzey yönü oku
    all_x = [r.x + r.width for r in plan.rooms]
    all_y = [r.y + r.height for r in plan.rooms]
    max_x = max(all_x) if all_x else 10
    max_y = max(all_y) if all_y else 10
    ax.annotate("K", xy=(max_x + 1.5, max_y),
                xytext=(max_x + 1.5, max_y - 1.5),
                fontsize=12, fontweight="bold", color="red", ha="center",
                arrowprops=dict(arrowstyle="->", color="red", lw=2), zorder=20)

    # Ölçek çubuğu
    min_x = min(r.x for r in plan.rooms)
    min_y = min(r.y for r in plan.rooms)
    scale_x = min_x
    scale_y = min_y - 2.0
    ax.plot([scale_x, scale_x + 5], [scale_y, scale_y], "k-", lw=2)
    ax.plot([scale_x, scale_x], [scale_y - 0.1, scale_y + 0.1], "k-", lw=2)
    ax.plot([scale_x + 5, scale_x + 5], [scale_y - 0.1, scale_y + 0.1],
            "k-", lw=2)
    ax.text(scale_x + 2.5, scale_y - 0.4, f"5 m ({scale})",
            ha="center", fontsize=8, color="#333")

    ax.set_aspect("equal")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, alpha=0.15, linestyle="--")
    ax.set_xlabel("x (metre)")
    ax.set_ylabel("y (metre)")
    fig.tight_layout()
    return fig


def _draw_thick_walls(ax, room: PlanRoom, plan: FloorPlan):
    """Duvar kalınlığını gerçekçi çizer."""
    x, y, w, h = room.x, room.y, room.width, room.height
    all_rooms = plan.rooms if plan else []

    min_x_all = min(r.x for r in all_rooms) if all_rooms else x
    max_x_all = max(r.x + r.width for r in all_rooms) if all_rooms else x + w
    min_y_all = min(r.y for r in all_rooms) if all_rooms else y
    max_y_all = max(r.y + r.height for r in all_rooms) if all_rooms else y + h

    is_exterior = {
        "south": abs(y - min_y_all) < 0.3,
        "north": abs(y + h - max_y_all) < 0.3,
        "west": abs(x - min_x_all) < 0.3,
        "east": abs(x + w - max_x_all) < 0.3,
    }

    walls = [
        ("south", [x, y], [x + w, y], True),
        ("north", [x, y + h], [x + w, y + h], True),
        ("west",  [x, y], [x, y + h], False),
        ("east",  [x + w, y], [x + w, y + h], False),
    ]

    for wall_name, start, end, is_horizontal in walls:
        is_ext = is_exterior.get(wall_name, False)
        thickness = DIS_DUVAR_KALINLIK if is_ext else IC_BOLME_DUVAR_KALINLIK
        color = "#1a1a1a" if is_ext else "#555"
        lw = 3.0 if is_ext else 1.2

        ax.plot([start[0], end[0]], [start[1], end[1]],
                color=color, lw=lw, zorder=5, solid_capstyle='projecting')

        # Dış duvar kalınlık gösterimi
        if is_ext:
            t = thickness / 2
            if is_horizontal:
                offset = -t if wall_name == "south" else 0
                wall_rect = mpatches.Rectangle(
                    (start[0], start[1] + offset),
                    abs(end[0] - start[0]), thickness,
                    linewidth=0.3, edgecolor=color,
                    facecolor="#D7CCC8", alpha=0.6, zorder=4)
            else:
                offset = -t if wall_name == "west" else 0
                wall_rect = mpatches.Rectangle(
                    (start[0] + offset, start[1]),
                    thickness, abs(end[1] - start[1]),
                    linewidth=0.3, edgecolor=color,
                    facecolor="#D7CCC8", alpha=0.6, zorder=4)
            ax.add_patch(wall_rect)


def _draw_dimensions_smart(ax, room: PlanRoom, tracker: dict):
    """Akıllı ölçü çizgileri — üst üste binmeyi önler."""
    x, y, w, h = room.x, room.y, room.width, room.height

    key_bottom = f"bottom_{y:.1f}"
    count = tracker.get(key_bottom, 0)
    offset = 0.35 + count * 0.45
    tracker[key_bottom] = count + 1

    if w >= 1.5:
        ax.annotate("", xy=(x + w, y - offset), xytext=(x, y - offset),
                    arrowprops=dict(arrowstyle="<->", color="#999", lw=0.5))
        ax.text(x + w / 2, y - offset - 0.18, f"{w:.2f}",
                ha="center", fontsize=6, color="#999")

    key_left = f"left_{x:.1f}"
    count = tracker.get(key_left, 0)
    offset_l = 0.35 + count * 0.45
    tracker[key_left] = count + 1

    if h >= 1.5:
        ax.annotate("", xy=(x - offset_l, y + h), xytext=(x - offset_l, y),
                    arrowprops=dict(arrowstyle="<->", color="#999", lw=0.5))
        ax.text(x - offset_l - 0.25, y + h / 2, f"{h:.2f}",
                ha="center", va="center", fontsize=6, color="#999",
                rotation=90)


def _draw_door(ax, room: PlanRoom, door: dict):
    """Kapı sembolü çiz (yay + duvar boşluğu)."""
    wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    width = door.get("width", 0.90)
    x, y, w, h = room.x, room.y, room.width, room.height

    if wall == "north":
        dx, dy = x + w * pos, y + h
        angle1, angle2 = 0, 90
        ax.plot([dx - width / 2, dx + width / 2], [dy, dy],
                color="white", lw=4, zorder=6)
    elif wall == "south":
        dx, dy = x + w * pos, y
        angle1, angle2 = 270, 360
        ax.plot([dx - width / 2, dx + width / 2], [dy, dy],
                color="white", lw=4, zorder=6)
    elif wall == "east":
        dx, dy = x + w, y + h * pos
        angle1, angle2 = 90, 180
        ax.plot([dx, dx], [dy - width / 2, dy + width / 2],
                color="white", lw=4, zorder=6)
    elif wall == "west":
        dx, dy = x, y + h * pos
        angle1, angle2 = 0, 90
        ax.plot([dx, dx], [dy - width / 2, dy + width / 2],
                color="white", lw=4, zorder=6)
    else:
        return

    arc = Arc((dx, dy), width, width, angle=0,
              theta1=angle1, theta2=angle2,
              color="#E65100", linewidth=1.2, linestyle="--", zorder=7)
    ax.add_patch(arc)


def _draw_window(ax, room: PlanRoom, window: dict):
    """Pencere sembolü — çift çizgi + orta cam çizgisi."""
    wall = window.get("wall", "south")
    pos = window.get("position", 0.5)
    width = window.get("width", 1.20)
    x, y, w, h = room.x, room.y, room.width, room.height
    gap = 0.08

    if wall == "south":
        wx = x + w * pos - width / 2
        ax.plot([wx, wx + width], [y, y], color="white", lw=4, zorder=6)
        ax.plot([wx, wx + width], [y, y], color="#1E88E5", lw=3, zorder=7)
        ax.plot([wx, wx + width], [y - gap, y - gap],
                color="#1E88E5", lw=1, zorder=7)
        mid_x = wx + width / 2
        ax.plot([mid_x, mid_x], [y - gap, y + gap],
                color="#1E88E5", lw=0.5, zorder=7)
    elif wall == "north":
        wx = x + w * pos - width / 2
        ax.plot([wx, wx + width], [y + h, y + h],
                color="white", lw=4, zorder=6)
        ax.plot([wx, wx + width], [y + h, y + h],
                color="#1E88E5", lw=3, zorder=7)
        ax.plot([wx, wx + width], [y + h + gap, y + h + gap],
                color="#1E88E5", lw=1, zorder=7)
    elif wall == "east":
        wy = y + h * pos - width / 2
        ax.plot([x + w, x + w], [wy, wy + width],
                color="white", lw=4, zorder=6)
        ax.plot([x + w, x + w], [wy, wy + width],
                color="#1E88E5", lw=3, zorder=7)
        ax.plot([x + w + gap, x + w + gap], [wy, wy + width],
                color="#1E88E5", lw=1, zorder=7)
    elif wall == "west":
        wy = y + h * pos - width / 2
        ax.plot([x, x], [wy, wy + width], color="white", lw=4, zorder=6)
        ax.plot([x, x], [wy, wy + width], color="#1E88E5", lw=3, zorder=7)
        ax.plot([x - gap, x - gap], [wy, wy + width],
                color="#1E88E5", lw=1, zorder=7)


def _draw_kitchen_counter(ax, room: PlanRoom):
    """Mutfak tezgah sembolü — tezgah + ocak + lavabo."""
    x, y, w, h = room.x, room.y, room.width, room.height
    t_depth = 0.55
    t_color = "#8D6E63"
    t_fill = "#EFEBE9"

    window_walls = [win.get("wall", "") for win in room.windows]

    if "south" in window_walls:
        counter = mpatches.Rectangle(
            (x + 0.1, y + h - t_depth), w * 0.7, t_depth,
            linewidth=0.8, edgecolor=t_color, facecolor=t_fill, zorder=8)
        ax.add_patch(counter)
        oc_x = x + 0.1 + w * 0.3
        oc_y = y + h - t_depth / 2
        for dx, dy in [(0, 0), (0.2, 0), (0, 0.15), (0.2, 0.15)]:
            circle = plt.Circle((oc_x + dx, oc_y + dy), 0.06,
                                color=t_color, fill=False, lw=0.5, zorder=9)
            ax.add_patch(circle)
        lav_x = x + 0.1 + w * 0.55
        ax.add_patch(mpatches.Ellipse(
            (lav_x, oc_y), 0.25, 0.18,
            linewidth=0.5, edgecolor=t_color, facecolor="white", zorder=9))
    else:
        counter = mpatches.Rectangle(
            (x + 0.1, y), w * 0.7, t_depth,
            linewidth=0.8, edgecolor=t_color, facecolor=t_fill, zorder=8)
        ax.add_patch(counter)
        oc_x = x + 0.1 + w * 0.3
        oc_y = y + t_depth / 2
        for dx, dy in [(0, 0), (0.2, 0), (0, 0.15), (0.2, 0.15)]:
            circle = plt.Circle((oc_x + dx, oc_y + dy), 0.06,
                                color=t_color, fill=False, lw=0.5, zorder=9)
            ax.add_patch(circle)


def _draw_staircase(ax, room: PlanRoom):
    """Merdiven sembolü — basamak çizgileri ve yön oku."""
    x, y, w, h = room.x, room.y, room.width, room.height

    num_steps = max(3, int(h / 0.27))
    step_h = h / num_steps
    for i in range(num_steps):
        step_y = y + i * step_h
        ax.plot([x + 0.1, x + w - 0.1], [step_y, step_y],
                color="#795548", lw=0.5, zorder=8)

    mid_x = x + w / 2
    ax.plot([mid_x, mid_x], [y, y + h], color="#795548",
            lw=1.0, linestyle="--", zorder=8)

    ax.annotate("", xy=(mid_x, y + h - 0.3), xytext=(mid_x, y + 0.3),
                arrowprops=dict(arrowstyle="->", color="#795548", lw=1.5),
                zorder=9)
    ax.text(x + w / 2, y + h / 2, "YK", ha="center", va="center",
            fontsize=7, color="#795548", fontweight="bold", zorder=10)


def _draw_furniture_item(ax, furn):
    """Tek mobilya öğesini plan üzerine çizer."""
    fx = furn.get("x", 0)
    fy = furn.get("y", 0)
    fw = furn.get("en", 0.5)
    fh = furn.get("boy", 0.5)
    name = furn.get("isim", "")
    sembol = furn.get("sembol", "")

    rect = mpatches.Rectangle(
        (fx, fy), fw, fh,
        linewidth=0.6, edgecolor="#8D6E63",
        facecolor="#EFEBE9", alpha=0.5, zorder=8)
    ax.add_patch(rect)

    if "yatak" in sembol:
        pillow_y = fy + fh - 0.25
        ax.add_patch(mpatches.Rectangle(
            (fx + 0.1, pillow_y), fw - 0.2, 0.15,
            linewidth=0.3, edgecolor="#8D6E63", facecolor="#FFF9C4", zorder=9))
    elif "klozet" in sembol:
        cx, cy = fx + fw / 2, fy + fh * 0.6
        ax.add_patch(mpatches.Ellipse(
            (cx, cy), fw * 0.7, fh * 0.5,
            linewidth=0.5, edgecolor="#8D6E63", facecolor="white", zorder=9))
    elif "dusakabin" in sembol:
        ax.plot([fx, fx + fw], [fy, fy + fh],
                color="#90CAF9", lw=0.5, zorder=9)
        ax.plot([fx + fw, fx], [fy, fy + fh],
                color="#90CAF9", lw=0.5, zorder=9)

    ax.text(fx + fw / 2, fy + fh / 2, name, ha="center", va="center",
            fontsize=4, color="#8D6E63", zorder=10)


def render_plan_comparison(plans: list[FloorPlan],
                            titles: list[str] = None) -> plt.Figure:
    """2-3 planı yan yana çizer."""
    n = len(plans)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 8))
    if n == 1:
        axes = [axes]

    for i, (plan, ax) in enumerate(zip(plans, axes)):
        title = (titles[i] if titles and i < len(titles)
                 else f"Alternatif {i + 1}")

        for room in plan.rooms:
            color = ROOM_COLORS.get(room.room_type, "#F5F5F5")
            rect = mpatches.Rectangle(
                (room.x, room.y), room.width, room.height,
                linewidth=2.0 if room.has_exterior_wall else 0.8,
                edgecolor="#333" if room.has_exterior_wall else "#666",
                facecolor=color, alpha=0.7, zorder=1)
            ax.add_patch(rect)

            if room.room_type in ("banyo", "wc"):
                hatch_r = mpatches.Rectangle(
                    (room.x, room.y), room.width, room.height,
                    linewidth=0, edgecolor=WET_HATCH_COLOR,
                    facecolor="none", hatch="///", alpha=0.3, zorder=2)
                ax.add_patch(hatch_r)

            cx, cy = room.center
            ax.text(cx, cy, f"{room.name}\n{room.area:.0f}m²",
                    ha="center", va="center", fontsize=6, color="#333",
                    zorder=10)

        ax.set_aspect("equal")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.15)
        ax.autoscale()

    fig.tight_layout()
    return fig
