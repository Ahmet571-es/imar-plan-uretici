"""
3D Bina Modeli Oluşturma — Plotly 3D ile interaktif görselleştirme.

İyileştirmeler:
- Pencere/kapı boşlukları (cam yüzey + çerçeve)
- Merdiven 3D modeli (basamaklar)
- Her daire farklı renk desteği
- Balkon korkuluk dikmeleri
"""

import numpy as np
import plotly.graph_objects as go
from core.plan_scorer import FloorPlan, PlanRoom
from utils.constants import (
    KAT_YUKSEKLIGI, IC_YUKSEKLIK, DOSEME_KALINLIK,
    DIS_DUVAR_KALINLIK, IC_BOLME_DUVAR_KALINLIK,
    PENCERE_ALT_SEVIYE, PENCERE_YUKSEKLIK,
    KAPI_YUKSEKLIK, BALKON_KORKULUK_YUKSEKLIK,
    MERDIVEN_BASAMAK_YUKSEKLIK, MERDIVEN_BASAMAK_GENISLIK,
)

# ── Renk paleti ──
FLOOR_COLORS = [
    "#E3F2FD", "#FFF3E0", "#E8F5E9", "#F3E5F5",
    "#FCE4EC", "#FFF9C4", "#E0F7FA", "#EFEBE9",
]

APARTMENT_COLORS = [
    "rgba(66,165,245,0.15)",
    "rgba(255,167,38,0.15)",
    "rgba(102,187,106,0.15)",
    "rgba(171,71,188,0.15)",
]

WALL_COLOR = "rgba(180,180,180,0.6)"
EXTERIOR_WALL_COLOR = "rgba(220,210,200,0.85)"
WINDOW_COLOR = "rgba(100,180,255,0.4)"
DOOR_COLOR = "rgba(139,90,43,0.7)"
FLOOR_SLAB_COLOR = "rgba(200,200,200,0.5)"
ROOF_COLOR = "rgba(180,80,60,0.7)"
GROUND_COLOR = "rgba(120,180,100,0.3)"
BALCONY_COLOR = "rgba(200,200,200,0.6)"
STAIR_COLOR = "rgba(160,120,80,0.7)"

# Oda tipi bazlı zemin renkleri (3D döşeme renklendirme)
ROOM_FLOOR_COLORS = {
    "salon":       "rgba(255,235,200,0.7)",   # Sıcak ahşap tonu
    "yatak_odasi": "rgba(220,230,255,0.7)",   # Açık mavi/huzurlu
    "mutfak":      "rgba(255,245,220,0.7)",   # Krem/fayans tonu
    "banyo":       "rgba(200,225,240,0.7)",   # Su mavisi
    "wc":          "rgba(210,230,240,0.7)",   # Açık mavi
    "antre":       "rgba(230,225,220,0.7)",   # Gri-bej
    "koridor":     "rgba(235,230,225,0.7)",   # Nötr gri
    "balkon":      "rgba(210,220,200,0.7)",   # Yeşilimsi
}

def _get_room_floor_color(room_type: str) -> str:
    """Oda tipine göre zemin rengi döndürür."""
    return ROOM_FLOOR_COLORS.get(room_type, "rgba(220,220,220,0.5)")


def build_3d_model(
    plans: list[FloorPlan],
    kat_sayisi: int = 4,
    parsel_coords: list[tuple[float, float]] | None = None,
    show_roof: bool = True,
    roof_type: str = "kirma",
    exploded: bool = False,
    explode_gap: float = 1.5,
    selected_floor: int | None = None,
    apartment_index: int | None = None,
) -> go.Figure:
    """3D bina modeli oluşturur."""
    fig = go.Figure()

    if len(plans) == 1:
        plans = plans * kat_sayisi

    for kat_idx in range(kat_sayisi):
        if selected_floor is not None and kat_idx != selected_floor:
            continue

        plan = plans[min(kat_idx, len(plans) - 1)]
        z_base = kat_idx * KAT_YUKSEKLIGI
        if exploded:
            z_base += kat_idx * explode_gap

        apt_color = (APARTMENT_COLORS[apartment_index % len(APARTMENT_COLORS)]
                     if apartment_index is not None else None)

        _add_floor_slab(fig, plan, z_base, kat_idx + 1)

        for room in plan.rooms:
            _add_room_walls(fig, room, z_base, kat_idx + 1, apt_color)

            for window in room.windows:
                _add_window_3d(fig, room, window, z_base)
            for door in room.doors:
                _add_door_3d(fig, room, door, z_base)
            if room.room_type == "balkon":
                _add_balcony_3d(fig, room, z_base)
            if room.room_type == "merdiven":
                _add_staircase_3d(fig, room, z_base, kat_idx + 1)

    if show_roof and (selected_floor is None):
        z_roof = kat_sayisi * KAT_YUKSEKLIGI
        if exploded:
            z_roof += kat_sayisi * explode_gap
        if plans:
            _add_roof(fig, plans[-1], z_roof, roof_type)

    if parsel_coords and (selected_floor is None or selected_floor == 0):
        _add_ground(fig, parsel_coords)

    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)", yaxis_title="Y (m)", zaxis_title="Z (m)",
            aspectmode="data",
            camera=dict(
                eye=dict(x=1.5, y=-1.5, z=1.0),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        title=dict(text=f"3D Bina Modeli — {kat_sayisi} Kat",
                   font=dict(size=16)),
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        height=700,
    )
    return fig


def _add_floor_slab(fig, plan, z_base, kat_no):
    if not plan.rooms:
        return
    xs = [r.x for r in plan.rooms] + [r.x + r.width for r in plan.rooms]
    ys = [r.y for r in plan.rooms] + [r.y + r.height for r in plan.rooms]
    x_min, x_max = min(xs) - 0.1, max(xs) + 0.1
    y_min, y_max = min(ys) - 0.1, max(ys) + 0.1
    vx = [x_min, x_max, x_max, x_min]
    vy = [y_min, y_min, y_max, y_max]
    fig.add_trace(go.Mesh3d(
        x=vx * 2, y=vy * 2,
        z=[z_base] * 4 + [z_base + DOSEME_KALINLIK] * 4,
        i=[0, 0, 4, 4, 0, 1, 2, 3, 4, 5, 6, 7],
        j=[1, 2, 5, 6, 1, 5, 6, 7, 0, 1, 2, 3],
        k=[2, 3, 6, 7, 4, 4, 5, 4, 3, 2, 5, 6],
        color=FLOOR_SLAB_COLOR, flatshading=True,
        name=f"Doseme Kat {kat_no}", hoverinfo="name",
    ))


def _add_room_walls(fig, room, z_base, kat_no, apt_color=None):
    x, y = room.x, room.y
    w, h = room.width, room.height
    z_floor = z_base + DOSEME_KALINLIK
    z_ceil = z_base + KAT_YUKSEKLIGI
    color = apt_color or (EXTERIOR_WALL_COLOR if room.has_exterior_wall
                          else WALL_COLOR)
    walls = [
        ([x, x + w, x + w, x], [y, y, y, y], [z_floor, z_floor, z_ceil, z_ceil]),
        ([x, x + w, x + w, x], [y + h, y + h, y + h, y + h],
         [z_floor, z_floor, z_ceil, z_ceil]),
        ([x, x, x, x], [y, y + h, y + h, y], [z_floor, z_floor, z_ceil, z_ceil]),
        ([x + w, x + w, x + w, x + w], [y, y + h, y + h, y],
         [z_floor, z_floor, z_ceil, z_ceil]),
    ]
    for wx, wy, wz in walls:
        fig.add_trace(go.Mesh3d(
            x=wx, y=wy, z=wz,
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=color, flatshading=True,
            name=f"{room.name} (Kat {kat_no})",
            hoverinfo="name", opacity=0.5,
        ))


def _add_window_3d(fig, room, window, z_base):
    wall = window.get("wall", "south")
    pos = window.get("position", 0.5)
    w_width = window.get("width", 1.20)
    z_sill = z_base + DOSEME_KALINLIK + PENCERE_ALT_SEVIYE
    z_top = z_sill + PENCERE_YUKSEKLIK
    x, y, rw, rh = room.x, room.y, room.width, room.height

    if wall == "south":
        ws = x + rw * pos - w_width / 2
        vx = [ws, ws + w_width, ws + w_width, ws]
        vy = [y, y, y, y]
    elif wall == "north":
        ws = x + rw * pos - w_width / 2
        vx = [ws, ws + w_width, ws + w_width, ws]
        vy = [y + rh, y + rh, y + rh, y + rh]
    elif wall == "east":
        ws = y + rh * pos - w_width / 2
        vx = [x + rw, x + rw, x + rw, x + rw]
        vy = [ws, ws + w_width, ws + w_width, ws]
    elif wall == "west":
        ws = y + rh * pos - w_width / 2
        vx = [x, x, x, x]
        vy = [ws, ws + w_width, ws + w_width, ws]
    else:
        return

    vz = [z_sill, z_sill, z_top, z_top]
    fig.add_trace(go.Mesh3d(
        x=vx, y=vy, z=vz,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=WINDOW_COLOR, flatshading=True,
        name="Pencere", hoverinfo="name", opacity=0.4,
    ))
    # Pencere çerçevesi
    fig.add_trace(go.Scatter3d(
        x=vx + [vx[0]], y=vy + [vy[0]], z=vz + [vz[0]],
        mode="lines", line=dict(color="rgba(30,136,229,0.8)", width=2),
        name="Pencere Cerceve", hoverinfo="none", showlegend=False,
    ))


def _add_door_3d(fig, room, door, z_base):
    wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    d_width = door.get("width", 0.90)
    z_floor = z_base + DOSEME_KALINLIK
    z_top = z_floor + KAPI_YUKSEKLIK
    x, y, rw, rh = room.x, room.y, room.width, room.height

    if wall == "south":
        ds = x + rw * pos - d_width / 2
        vx = [ds, ds + d_width, ds + d_width, ds]
        vy = [y, y, y, y]
    elif wall == "north":
        ds = x + rw * pos - d_width / 2
        vx = [ds, ds + d_width, ds + d_width, ds]
        vy = [y + rh, y + rh, y + rh, y + rh]
    elif wall == "east":
        ds = y + rh * pos - d_width / 2
        vx = [x + rw, x + rw, x + rw, x + rw]
        vy = [ds, ds + d_width, ds + d_width, ds]
    elif wall == "west":
        ds = y + rh * pos - d_width / 2
        vx = [x, x, x, x]
        vy = [ds, ds + d_width, ds + d_width, ds]
    else:
        return

    fig.add_trace(go.Mesh3d(
        x=vx, y=vy, z=[z_floor, z_floor, z_top, z_top],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=DOOR_COLOR, flatshading=True,
        name="Kapi", hoverinfo="name", opacity=0.6,
    ))


def _add_balcony_3d(fig, room, z_base):
    x, y, w, h = room.x, room.y, room.width, room.height
    z_floor = z_base + DOSEME_KALINLIK
    z_railing = z_floor + BALKON_KORKULUK_YUKSEKLIK

    fig.add_trace(go.Mesh3d(
        x=[x, x + w, x + w, x] * 2,
        y=[y, y, y + h, y + h] * 2,
        z=[z_floor] * 4 + [z_floor + 0.15] * 4,
        i=[0, 0, 4, 4], j=[1, 2, 5, 6], k=[2, 3, 6, 7],
        color=BALCONY_COLOR, flatshading=True,
        name="Balkon", hoverinfo="name", opacity=0.6,
    ))
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    fig.add_trace(go.Scatter3d(
        x=[p[0] for p in pts], y=[p[1] for p in pts],
        z=[z_railing] * len(pts),
        mode="lines", line=dict(color="gray", width=4),
        name="Korkuluk", hoverinfo="none", showlegend=False,
    ))
    for px, py in pts[:-1]:
        fig.add_trace(go.Scatter3d(
            x=[px, px], y=[py, py], z=[z_floor, z_railing],
            mode="lines", line=dict(color="gray", width=2),
            hoverinfo="none", showlegend=False,
        ))


def _add_staircase_3d(fig, room, z_base, kat_no):
    """Merdiven 3D modeli — basamaklar."""
    x, y, w, h = room.x, room.y, room.width, room.height
    z_floor = z_base + DOSEME_KALINLIK
    num_steps = int(KAT_YUKSEKLIGI / MERDIVEN_BASAMAK_YUKSEKLIK)
    half = num_steps // 2
    step_d = (h * 0.45) / max(half, 1)

    for i in range(half):
        z_s = z_floor + i * MERDIVEN_BASAMAK_YUKSEKLIK
        sy = y + i * step_d
        sx = [x + 0.1, x + w / 2 - 0.1, x + w / 2 - 0.1, x + 0.1]
        s_y = [sy, sy, sy + step_d, sy + step_d]
        fig.add_trace(go.Mesh3d(
            x=sx * 2, y=s_y * 2,
            z=[z_s] * 4 + [z_s + MERDIVEN_BASAMAK_YUKSEKLIK] * 4,
            i=[0, 0, 4, 4], j=[1, 2, 5, 6], k=[2, 3, 6, 7],
            color=STAIR_COLOR, flatshading=True,
            name=f"Merdiven Kat {kat_no}", hoverinfo="name",
            opacity=0.7, showlegend=False,
        ))

    sahanlık_y = y + half * step_d
    for i in range(half):
        z_s = z_floor + (half + i) * MERDIVEN_BASAMAK_YUKSEKLIK
        sy = sahanlık_y + h * 0.1 + (half - 1 - i) * step_d
        sx = [x + w / 2 + 0.1, x + w - 0.1, x + w - 0.1, x + w / 2 + 0.1]
        s_y = [sy, sy, sy + step_d, sy + step_d]
        fig.add_trace(go.Mesh3d(
            x=sx * 2, y=s_y * 2,
            z=[z_s] * 4 + [z_s + MERDIVEN_BASAMAK_YUKSEKLIK] * 4,
            i=[0, 0, 4, 4], j=[1, 2, 5, 6], k=[2, 3, 6, 7],
            color=STAIR_COLOR, flatshading=True,
            hoverinfo="name", opacity=0.7, showlegend=False,
        ))


def _add_roof(fig, plan, z_base, roof_type="kirma"):
    if not plan.rooms:
        return
    xs = [r.x for r in plan.rooms] + [r.x + r.width for r in plan.rooms]
    ys = [r.y for r in plan.rooms] + [r.y + r.height for r in plan.rooms]
    x_min, x_max = min(xs) - 0.3, max(xs) + 0.3
    y_min, y_max = min(ys) - 0.3, max(ys) + 0.3
    x_mid = (x_min + x_max) / 2

    if roof_type == "kirma":
        rh = min(x_max - x_min, y_max - y_min) * 0.2
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_max, x_max, x_min, x_mid, x_mid],
            y=[y_min, y_min, y_max, y_max, y_min, y_max],
            z=[z_base] * 4 + [z_base + rh] * 2,
            i=[0, 1, 2, 3, 0, 2], j=[1, 2, 3, 0, 4, 5], k=[4, 5, 5, 4, 1, 3],
            color=ROOF_COLOR, flatshading=True,
            name="Cati", hoverinfo="name", opacity=0.7,
        ))
    else:
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_max, x_max, x_min],
            y=[y_min, y_min, y_max, y_max],
            z=[z_base + 0.1] * 4,
            i=[0, 0], j=[1, 2], k=[2, 3],
            color="rgba(180,180,180,0.5)", flatshading=True,
            name="Teras Cati", hoverinfo="name",
        ))


def _add_ground(fig, parsel_coords):
    if not parsel_coords or len(parsel_coords) < 3:
        return
    xs = [c[0] for c in parsel_coords]
    ys = [c[1] for c in parsel_coords]
    n = len(xs)
    i_l, j_l, k_l = [], [], []
    for idx in range(1, n - 1):
        i_l.append(0)
        j_l.append(idx)
        k_l.append(idx + 1)
    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=[0.0] * n,
        i=i_l, j=j_l, k=k_l,
        color=GROUND_COLOR, flatshading=True,
        name="Parsel", hoverinfo="name", opacity=0.3,
    ))


def build_dual_apartment_3d(dual_plan: dict, kat_sayisi: int = 4,
                             **kwargs) -> go.Figure:
    """2 daireli bina 3D modeli — her daire farklı renk."""
    fig = go.Figure()
    apt1 = dual_plan.get("apartment_1")
    apt2 = dual_plan.get("apartment_2")
    stairwell = dual_plan.get("stairwell")

    for kat_idx in range(kat_sayisi):
        z_base = kat_idx * KAT_YUKSEKLIGI
        _add_floor_slab(fig, apt1, z_base, kat_idx + 1)

        for room in apt1.rooms:
            _add_room_walls(fig, room, z_base, kat_idx + 1,
                            apt_color=APARTMENT_COLORS[0])
            for win in room.windows:
                _add_window_3d(fig, room, win, z_base)
            for door in room.doors:
                _add_door_3d(fig, room, door, z_base)
            if room.room_type == "balkon":
                _add_balcony_3d(fig, room, z_base)

        for room in apt2.rooms:
            _add_room_walls(fig, room, z_base, kat_idx + 1,
                            apt_color=APARTMENT_COLORS[1])
            for win in room.windows:
                _add_window_3d(fig, room, win, z_base)
            for door in room.doors:
                _add_door_3d(fig, room, door, z_base)
            if room.room_type == "balkon":
                _add_balcony_3d(fig, room, z_base)

        if stairwell:
            _add_staircase_3d(fig, stairwell, z_base, kat_idx + 1)

    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)", yaxis_title="Y (m)", zaxis_title="Z (m)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.0)),
        ),
        title=dict(text=f"3D Bina — 2 Daire x {kat_sayisi} Kat",
                   font=dict(size=16)),
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        height=700,
    )
    return fig
