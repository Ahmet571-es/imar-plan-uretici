"""
Kat Planı Matplotlib Çizimi — 2D plan görselleştirme.
"""

import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc, FancyArrowPatch
from core.plan_scorer import FloorPlan, PlanRoom

# Oda tipi renk paleti
ROOM_COLORS = {
    "salon":       "#E3F2FD",
    "yatak_odasi": "#FFF3E0",
    "mutfak":      "#E8F5E9",
    "banyo":       "#F3E5F5",
    "wc":          "#FCE4EC",
    "antre":       "#FFF9C4",
    "koridor":     "#F5F5F5",
    "balkon":      "#E0F7FA",
    "depo":        "#EFEBE9",
    "diger":       "#F5F5F5",
}

ROOM_HATCH = {
    "banyo": "//",
    "wc":    "//",
}


def render_floor_plan(
    plan: FloorPlan,
    title: str = "Kat Planı",
    show_dimensions: bool = True,
    show_doors: bool = True,
    show_windows: bool = True,
    show_furniture: bool = False,
    figsize: tuple = (12, 10),
    scale: str = "1:100",
) -> plt.Figure:
    """Kat planını matplotlib ile çizer.

    Args:
        plan: FloorPlan nesnesi.
        title: Başlık.
        show_dimensions: Ölçü çizgilerini göster.
        show_doors: Kapıları göster.
        show_windows: Pencereleri göster.
        show_furniture: Mobilya sembollerini göster.
        figsize: Figür boyutu.
        scale: Çizim ölçeği metni.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    if not plan.rooms:
        ax.text(0.5, 0.5, "Plan verisi yok", transform=ax.transAxes,
                ha="center", va="center", fontsize=16, color="#999")
        return fig

    # ── Odaları çiz ──
    for room in plan.rooms:
        color = ROOM_COLORS.get(room.room_type, "#F5F5F5")
        hatch = ROOM_HATCH.get(room.room_type, None)

        # Oda dikdörtgeni
        rect = mpatches.Rectangle(
            (room.x, room.y), room.width, room.height,
            linewidth=1.5 if room.has_exterior_wall else 0.8,
            edgecolor="#333" if room.has_exterior_wall else "#666",
            facecolor=color,
            hatch=hatch,
            alpha=0.7,
        )
        ax.add_patch(rect)

        # Dış duvarlar kalın çizgi
        if room.has_exterior_wall:
            _draw_exterior_walls(ax, room)

        # Oda ismi
        cx, cy = room.center
        ax.text(cx, cy + 0.15, room.name,
                ha="center", va="center",
                fontsize=8, fontweight="bold", color="#333")

        # Oda alanı
        ax.text(cx, cy - 0.35, f"{room.area:.1f} m²",
                ha="center", va="center",
                fontsize=7, color="#666", style="italic")

        # Ölçü çizgileri
        if show_dimensions:
            _draw_dimensions(ax, room)

        # Kapılar
        if show_doors and room.doors:
            for door in room.doors:
                _draw_door(ax, room, door)

        # Pencereler
        if show_windows and room.windows:
            for window in room.windows:
                _draw_window(ax, room, window)

    # ── Kuzey yönü oku ──
    all_x = [r.x + r.width for r in plan.rooms]
    all_y = [r.y + r.height for r in plan.rooms]
    max_x = max(all_x) if all_x else 10
    max_y = max(all_y) if all_y else 10
    ax.annotate("K", xy=(max_x + 1.5, max_y),
                xytext=(max_x + 1.5, max_y - 1.5),
                fontsize=12, fontweight="bold", color="red",
                ha="center",
                arrowprops=dict(arrowstyle="->", color="red", lw=2))

    # ── Ölçek çubuğu ──
    scale_x = 0.5
    scale_y = -1.5
    ax.plot([scale_x, scale_x + 5], [scale_y, scale_y], "k-", lw=2)
    ax.plot([scale_x, scale_x], [scale_y - 0.1, scale_y + 0.1], "k-", lw=2)
    ax.plot([scale_x + 5, scale_x + 5], [scale_y - 0.1, scale_y + 0.1], "k-", lw=2)
    ax.text(scale_x + 2.5, scale_y - 0.4, f"5 m ({scale})",
            ha="center", fontsize=8, color="#333")

    ax.set_aspect("equal")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, alpha=0.15, linestyle="--")
    ax.set_xlabel("x (metre)")
    ax.set_ylabel("y (metre)")

    fig.tight_layout()
    return fig


def _draw_exterior_walls(ax, room: PlanRoom):
    """Dış duvarları kalın çizgiyle çiz."""
    x, y, w, h = room.x, room.y, room.width, room.height
    lw = 3.0
    color = "#1a1a1a"

    # Basit: tüm kenarlar dış duvar (has_exterior_wall true ise)
    ax.plot([x, x+w], [y, y], color=color, lw=lw)
    ax.plot([x, x+w], [y+h, y+h], color=color, lw=lw)
    ax.plot([x, x], [y, y+h], color=color, lw=lw)
    ax.plot([x+w, x+w], [y, y+h], color=color, lw=lw)


def _draw_dimensions(ax, room: PlanRoom):
    """Oda boyut ölçülerini çiz."""
    x, y, w, h = room.x, room.y, room.width, room.height
    offset = 0.25

    # Genişlik (alt)
    ax.annotate("", xy=(x + w, y - offset), xytext=(x, y - offset),
                arrowprops=dict(arrowstyle="<->", color="#999", lw=0.5))
    ax.text(x + w/2, y - offset - 0.2, f"{w:.2f}",
            ha="center", fontsize=6, color="#999")

    # Yükseklik (sol)
    ax.annotate("", xy=(x - offset, y + h), xytext=(x - offset, y),
                arrowprops=dict(arrowstyle="<->", color="#999", lw=0.5))
    ax.text(x - offset - 0.3, y + h/2, f"{h:.2f}",
            ha="center", va="center", fontsize=6, color="#999", rotation=90)


def _draw_door(ax, room: PlanRoom, door: dict):
    """Kapı sembolü çiz (yay)."""
    wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    width = door.get("width", 0.90)
    x, y, w, h = room.x, room.y, room.width, room.height

    if wall == "north":
        dx = x + w * pos
        dy = y + h
        angle1, angle2 = 0, 90
    elif wall == "south":
        dx = x + w * pos
        dy = y
        angle1, angle2 = 270, 360
    elif wall == "east":
        dx = x + w
        dy = y + h * pos
        angle1, angle2 = 90, 180
    elif wall == "west":
        dx = x
        dy = y + h * pos
        angle1, angle2 = 0, 90
    else:
        return

    arc = Arc((dx, dy), width, width, angle=0,
              theta1=angle1, theta2=angle2,
              color="#E65100", linewidth=1.0, linestyle="--")
    ax.add_patch(arc)


def _draw_window(ax, room: PlanRoom, window: dict):
    """Pencere sembolü çiz (çift çizgi)."""
    wall = window.get("wall", "south")
    pos = window.get("position", 0.5)
    width = window.get("width", 1.20)
    x, y, w, h = room.x, room.y, room.width, room.height
    gap = 0.08

    if wall == "south":
        wx = x + w * pos - width / 2
        ax.plot([wx, wx + width], [y, y], color="#1E88E5", lw=3)
        ax.plot([wx, wx + width], [y - gap, y - gap], color="#1E88E5", lw=1)
    elif wall == "north":
        wx = x + w * pos - width / 2
        ax.plot([wx, wx + width], [y + h, y + h], color="#1E88E5", lw=3)
        ax.plot([wx, wx + width], [y + h + gap, y + h + gap], color="#1E88E5", lw=1)
    elif wall == "east":
        wy = y + h * pos - width / 2
        ax.plot([x + w, x + w], [wy, wy + width], color="#1E88E5", lw=3)
        ax.plot([x + w + gap, x + w + gap], [wy, wy + width], color="#1E88E5", lw=1)
    elif wall == "west":
        wy = y + h * pos - width / 2
        ax.plot([x, x], [wy, wy + width], color="#1E88E5", lw=3)
        ax.plot([x - gap, x - gap], [wy, wy + width], color="#1E88E5", lw=1)


def render_plan_comparison(plans: list[FloorPlan], titles: list[str] = None) -> plt.Figure:
    """2-3 planı yan yana çizer."""
    n = len(plans)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 8))
    if n == 1:
        axes = [axes]

    for i, (plan, ax) in enumerate(zip(plans, axes)):
        title = titles[i] if titles and i < len(titles) else f"Alternatif {i+1}"

        for room in plan.rooms:
            color = ROOM_COLORS.get(room.room_type, "#F5F5F5")
            hatch = ROOM_HATCH.get(room.room_type, None)
            rect = mpatches.Rectangle(
                (room.x, room.y), room.width, room.height,
                linewidth=1.5 if room.has_exterior_wall else 0.8,
                edgecolor="#333" if room.has_exterior_wall else "#666",
                facecolor=color, hatch=hatch, alpha=0.7,
            )
            ax.add_patch(rect)
            cx, cy = room.center
            ax.text(cx, cy, f"{room.name}\n{room.area:.0f}m²",
                    ha="center", va="center", fontsize=6, color="#333")

        ax.set_aspect("equal")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.15)
        ax.autoscale()

    fig.tight_layout()
    return fig
