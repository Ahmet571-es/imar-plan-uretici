"""
3D Bina Modeli Oluşturma — Plotly 3D ile interaktif görselleştirme.
Kat planından duvarlar, pencereler, kapılar, balkonlar ve çatı modeli üretir.
"""

import numpy as np
import plotly.graph_objects as go
from core.plan_scorer import FloorPlan, PlanRoom
from utils.constants import (
    KAT_YUKSEKLIGI, IC_YUKSEKLIK, DOSEME_KALINLIK,
    DIS_DUVAR_KALINLIK, IC_BOLME_DUVAR_KALINLIK,
    PENCERE_ALT_SEVIYE, PENCERE_YUKSEKLIK,
    KAPI_YUKSEKLIK, BALKON_KORKULUK_YUKSEKLIK,
)

# ── Renk paleti ──
FLOOR_COLORS = [
    "#E3F2FD", "#FFF3E0", "#E8F5E9", "#F3E5F5",
    "#FCE4EC", "#FFF9C4", "#E0F7FA", "#EFEBE9",
]
WALL_COLOR = "rgba(180,180,180,0.6)"
EXTERIOR_WALL_COLOR = "rgba(220,210,200,0.85)"
WINDOW_COLOR = "rgba(100,180,255,0.4)"
DOOR_COLOR = "rgba(139,90,43,0.7)"
FLOOR_SLAB_COLOR = "rgba(200,200,200,0.5)"
ROOF_COLOR = "rgba(180,80,60,0.7)"
GROUND_COLOR = "rgba(120,180,100,0.3)"
BALCONY_COLOR = "rgba(200,200,200,0.6)"


def build_3d_model(
    plans: list[FloorPlan],
    kat_sayisi: int = 4,
    parsel_coords: list[tuple[float, float]] | None = None,
    show_roof: bool = True,
    roof_type: str = "kirma",  # "kirma" veya "teras"
    exploded: bool = False,
    explode_gap: float = 1.5,
    selected_floor: int | None = None,
) -> go.Figure:
    """3D bina modeli oluşturur.

    Args:
        plans: Her kat için FloorPlan listesi (tekse tüm katlarda aynı).
        kat_sayisi: Toplam kat sayısı.
        parsel_coords: Parsel sınır koordinatları (zemin gösterimi için).
        show_roof: Çatı göster.
        roof_type: Çatı tipi.
        exploded: Patlak görünüm (katlar aralıklı).
        explode_gap: Patlak görünüm kat arası boşluk.
        selected_floor: Sadece belirli bir kat göster (None=tümü).

    Returns:
        Plotly Figure nesnesi.
    """
    fig = go.Figure()

    # Plan tekse tüm katlarda kullan
    if len(plans) == 1:
        plans = plans * kat_sayisi

    for kat_idx in range(kat_sayisi):
        if selected_floor is not None and kat_idx != selected_floor:
            continue

        plan = plans[min(kat_idx, len(plans) - 1)]
        z_base = kat_idx * KAT_YUKSEKLIGI
        if exploded:
            z_base += kat_idx * explode_gap

        color_idx = kat_idx % len(FLOOR_COLORS)

        # ── Kat döşemesi ──
        _add_floor_slab(fig, plan, z_base, kat_idx + 1)

        # ── Her oda için duvar ve detaylar ──
        for room in plan.rooms:
            _add_room_walls(fig, room, z_base, kat_idx + 1)

            # Pencereler
            for window in room.windows:
                _add_window_3d(fig, room, window, z_base)

            # Kapılar
            for door in room.doors:
                _add_door_3d(fig, room, door, z_base)

            # Balkon
            if room.room_type == "balkon":
                _add_balcony_3d(fig, room, z_base)

    # ── Çatı ──
    if show_roof and (selected_floor is None):
        z_roof = kat_sayisi * KAT_YUKSEKLIGI
        if exploded:
            z_roof += kat_sayisi * explode_gap
        if plans:
            _add_roof(fig, plans[-1], z_roof, roof_type)

    # ── Zemin / Parsel ──
    if parsel_coords and (selected_floor is None or selected_floor == 0):
        _add_ground(fig, parsel_coords)

    # ── Layout ──
    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data",
            camera=dict(
                eye=dict(x=1.5, y=-1.5, z=1.0),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        title=dict(
            text=f"🏗️ 3D Bina Modeli — {kat_sayisi} Kat",
            font=dict(size=16),
        ),
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        height=700,
    )

    return fig


def _add_floor_slab(fig, plan: FloorPlan, z_base: float, kat_no: int):
    """Kat döşemesi ekler."""
    if not plan.rooms:
        return

    xs = [r.x for r in plan.rooms] + [r.x + r.width for r in plan.rooms]
    ys = [r.y for r in plan.rooms] + [r.y + r.height for r in plan.rooms]
    x_min, x_max = min(xs) - 0.1, max(xs) + 0.1
    y_min, y_max = min(ys) - 0.1, max(ys) + 0.1

    vertices_x = [x_min, x_max, x_max, x_min]
    vertices_y = [y_min, y_min, y_max, y_max]

    fig.add_trace(go.Mesh3d(
        x=vertices_x * 2,
        y=vertices_y * 2,
        z=[z_base] * 4 + [z_base + DOSEME_KALINLIK] * 4,
        i=[0, 0, 4, 4, 0, 1, 2, 3, 4, 5, 6, 7],
        j=[1, 2, 5, 6, 1, 5, 6, 7, 0, 1, 2, 3],
        k=[2, 3, 6, 7, 4, 4, 5, 4, 3, 2, 5, 6],
        color=FLOOR_SLAB_COLOR,
        flatshading=True,
        name=f"Döşeme Kat {kat_no}",
        hoverinfo="name",
    ))


def _add_room_walls(fig, room: PlanRoom, z_base: float, kat_no: int):
    """Oda duvarlarını 3D olarak ekler."""
    x, y = room.x, room.y
    w, h = room.width, room.height
    z_floor = z_base + DOSEME_KALINLIK
    z_ceil = z_base + KAT_YUKSEKLIGI
    wall_t = DIS_DUVAR_KALINLIK if room.has_exterior_wall else IC_BOLME_DUVAR_KALINLIK

    color = EXTERIOR_WALL_COLOR if room.has_exterior_wall else WALL_COLOR

    # 4 duvarı yüzey olarak ekle
    walls = [
        # Alt duvar (y=y)
        ([x, x+w, x+w, x], [y, y, y, y], [z_floor, z_floor, z_ceil, z_ceil]),
        # Üst duvar (y=y+h)
        ([x, x+w, x+w, x], [y+h, y+h, y+h, y+h], [z_floor, z_floor, z_ceil, z_ceil]),
        # Sol duvar (x=x)
        ([x, x, x, x], [y, y+h, y+h, y], [z_floor, z_floor, z_ceil, z_ceil]),
        # Sağ duvar (x=x+w)
        ([x+w, x+w, x+w, x+w], [y, y+h, y+h, y], [z_floor, z_floor, z_ceil, z_ceil]),
    ]

    for wx, wy, wz in walls:
        fig.add_trace(go.Mesh3d(
            x=wx, y=wy, z=wz,
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=color,
            flatshading=True,
            name=f"{room.name} (Kat {kat_no})",
            hoverinfo="name",
            opacity=0.5,
        ))


def _add_window_3d(fig, room: PlanRoom, window: dict, z_base: float):
    """Pencere 3D modeli ekler."""
    wall = window.get("wall", "south")
    pos = window.get("position", 0.5)
    w_width = window.get("width", 1.20)

    z_sill = z_base + DOSEME_KALINLIK + PENCERE_ALT_SEVIYE
    z_top = z_sill + PENCERE_YUKSEKLIK

    x, y = room.x, room.y
    rw, rh = room.width, room.height

    if wall == "south":
        wx_start = x + rw * pos - w_width / 2
        vx = [wx_start, wx_start + w_width, wx_start + w_width, wx_start]
        vy = [y, y, y, y]
    elif wall == "north":
        wx_start = x + rw * pos - w_width / 2
        vx = [wx_start, wx_start + w_width, wx_start + w_width, wx_start]
        vy = [y + rh, y + rh, y + rh, y + rh]
    elif wall == "east":
        wy_start = y + rh * pos - w_width / 2
        vx = [x + rw, x + rw, x + rw, x + rw]
        vy = [wy_start, wy_start + w_width, wy_start + w_width, wy_start]
    elif wall == "west":
        wy_start = y + rh * pos - w_width / 2
        vx = [x, x, x, x]
        vy = [wy_start, wy_start + w_width, wy_start + w_width, wy_start]
    else:
        return

    vz = [z_sill, z_sill, z_top, z_top]

    fig.add_trace(go.Mesh3d(
        x=vx, y=vy, z=vz,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=WINDOW_COLOR,
        flatshading=True,
        name="Pencere",
        hoverinfo="name",
        opacity=0.4,
    ))


def _add_door_3d(fig, room: PlanRoom, door: dict, z_base: float):
    """Kapı 3D modeli ekler."""
    wall = door.get("wall", "north")
    pos = door.get("position", 0.5)
    d_width = door.get("width", 0.90)

    z_floor = z_base + DOSEME_KALINLIK
    z_top = z_floor + KAPI_YUKSEKLIK

    x, y = room.x, room.y
    rw, rh = room.width, room.height

    if wall == "south":
        dx_start = x + rw * pos - d_width / 2
        vx = [dx_start, dx_start + d_width, dx_start + d_width, dx_start]
        vy = [y, y, y, y]
    elif wall == "north":
        dx_start = x + rw * pos - d_width / 2
        vx = [dx_start, dx_start + d_width, dx_start + d_width, dx_start]
        vy = [y + rh, y + rh, y + rh, y + rh]
    elif wall == "east":
        dy_start = y + rh * pos - d_width / 2
        vx = [x + rw, x + rw, x + rw, x + rw]
        vy = [dy_start, dy_start + d_width, dy_start + d_width, dy_start]
    elif wall == "west":
        dy_start = y + rh * pos - d_width / 2
        vx = [x, x, x, x]
        vy = [dy_start, dy_start + d_width, dy_start + d_width, dy_start]
    else:
        return

    vz = [z_floor, z_floor, z_top, z_top]

    fig.add_trace(go.Mesh3d(
        x=vx, y=vy, z=vz,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=DOOR_COLOR,
        flatshading=True,
        name="Kapı",
        hoverinfo="name",
        opacity=0.6,
    ))


def _add_balcony_3d(fig, room: PlanRoom, z_base: float):
    """Balkon 3D modeli ekler (döşeme + korkuluk)."""
    x, y = room.x, room.y
    w, h = room.width, room.height
    z_floor = z_base + DOSEME_KALINLIK
    z_railing = z_floor + BALKON_KORKULUK_YUKSEKLIK

    # Döşeme
    fig.add_trace(go.Mesh3d(
        x=[x, x+w, x+w, x] * 2,
        y=[y, y, y+h, y+h] * 2,
        z=[z_floor]*4 + [z_floor + 0.15]*4,
        i=[0, 0, 4, 4], j=[1, 2, 5, 6], k=[2, 3, 6, 7],
        color=BALCONY_COLOR, flatshading=True,
        name="Balkon", hoverinfo="name", opacity=0.6,
    ))

    # Korkuluk çizgileri
    railing_pts = [
        (x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)
    ]
    rx = [p[0] for p in railing_pts]
    ry = [p[1] for p in railing_pts]
    rz = [z_railing] * len(railing_pts)

    fig.add_trace(go.Scatter3d(
        x=rx, y=ry, z=rz,
        mode="lines",
        line=dict(color="gray", width=4),
        name="Korkuluk",
        hoverinfo="none",
    ))


def _add_roof(fig, plan: FloorPlan, z_base: float, roof_type: str = "kirma"):
    """Çatı modeli ekler."""
    if not plan.rooms:
        return

    xs = [r.x for r in plan.rooms] + [r.x + r.width for r in plan.rooms]
    ys = [r.y for r in plan.rooms] + [r.y + r.height for r in plan.rooms]
    x_min, x_max = min(xs) - 0.3, max(xs) + 0.3
    y_min, y_max = min(ys) - 0.3, max(ys) + 0.3
    x_mid = (x_min + x_max) / 2
    y_mid = (y_min + y_max) / 2

    if roof_type == "kirma":
        # Kırma çatı — mahya yüksekliği
        roof_height = min((x_max - x_min), (y_max - y_min)) * 0.2
        z_peak = z_base + roof_height

        # 4 yüzey
        vx = [x_min, x_max, x_max, x_min, x_mid, x_mid]
        vy = [y_min, y_min, y_max, y_max, y_min, y_max]
        vz = [z_base, z_base, z_base, z_base, z_peak, z_peak]

        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz,
            i=[0, 1, 2, 3, 0, 2],
            j=[1, 2, 3, 0, 4, 5],
            k=[4, 5, 5, 4, 1, 3],
            color=ROOF_COLOR,
            flatshading=True,
            name="Çatı",
            hoverinfo="name",
            opacity=0.7,
        ))
    else:
        # Teras çatı — düz
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_max, x_max, x_min],
            y=[y_min, y_min, y_max, y_max],
            z=[z_base + 0.1] * 4,
            i=[0, 0], j=[1, 2], k=[2, 3],
            color="rgba(180,180,180,0.5)",
            flatshading=True,
            name="Teras Çatı",
            hoverinfo="name",
        ))


def _add_ground(fig, parsel_coords):
    """Zemin/parsel gösterimi."""
    if not parsel_coords or len(parsel_coords) < 3:
        return

    xs = [c[0] for c in parsel_coords]
    ys = [c[1] for c in parsel_coords]
    zs = [0.0] * len(parsel_coords)

    # Basit triangulation
    n = len(xs)
    i_list, j_list, k_list = [], [], []
    for idx in range(1, n - 1):
        i_list.append(0)
        j_list.append(idx)
        k_list.append(idx + 1)

    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=zs,
        i=i_list, j=j_list, k=k_list,
        color=GROUND_COLOR,
        flatshading=True,
        name="Parsel",
        hoverinfo="name",
        opacity=0.3,
    ))
