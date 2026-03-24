"""
Ajan 5 — Plan Optimizasyon: Yüzlerce plan varyasyonu üretip en iyisini seçer.
Dış API gerektirmez — mevcut plan_scorer + demo planner kullanır.
"""

import math
import random
import logging
from agents.base_agent import BaseAgent
from core.plan_scorer import score_plan, FloorPlan, PlanRoom
from dataset.dataset_rules import (
    ROOM_SIZE_STATS, ROOM_ASPECT_RATIOS, ROOM_PLACEMENT_RULES,
    calculate_ideal_dimensions, get_adjacency_score,
)

logger = logging.getLogger(__name__)


class PlanOptimizasyonAjani(BaseAgent):
    """Gece boyunca yüzlerce plan varyasyonu üretip en iyisini seçer."""

    def __init__(self):
        super().__init__(
            name="plan_optimizasyon",
            description="Plan varyasyonları üretir, puanlar, en iyilerini seçer",
        )

    def execute(
        self,
        buildable_width: float = 16.0,
        buildable_height: float = 12.0,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
        apartment_type: str = "3+1",
        target_area: float = 120.0,
        iteration_count: int = 200,
        sun_direction: str = "south",
        **kwargs,
    ) -> dict:
        """Plan optimizasyonu çalıştırır.

        Args:
            buildable_width/height: Yapılaşma alanı boyutları.
            apartment_type: Daire tipi.
            target_area: Hedef daire alanı (m²).
            iteration_count: Deneme sayısı.
            sun_direction: En iyi güneş yönü.
        """
        self.logger.info(f"Plan optimizasyonu başlıyor — {iteration_count} iterasyon")

        # Oda programını belirle
        room_program = _get_room_program(apartment_type, target_area)

        all_plans = []
        best_score = 0
        best_plan = None

        for i in range(iteration_count):
            # Farklı stratejiler dene
            strategy = i % 5
            plan = _generate_variant(
                room_program, buildable_width, buildable_height,
                origin_x, origin_y, strategy, sun_direction,
            )

            if plan and plan.rooms:
                sc = score_plan(plan, sun_best_direction=sun_direction)
                all_plans.append({"plan": plan, "score": sc.total, "strategy": strategy})

                if sc.total > best_score:
                    best_score = sc.total
                    best_plan = plan

        # En iyi 5'i seç
        all_plans.sort(key=lambda x: x["score"], reverse=True)
        top_5 = all_plans[:5]

        # Puan dağılımı istatistikleri
        scores = [p["score"] for p in all_plans if p["score"] > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        summary = (
            f"{iteration_count} plan test edildi. "
            f"En iyi: {max_score:.1f}/100, Ortalama: {avg_score:.1f}/100, "
            f"En düşük: {min_score:.1f}/100. "
            f"Top 5 strateji: {[p['strategy'] for p in top_5]}"
        )

        return {
            "success": True,
            "items_found": len([p for p in all_plans if p["score"] > 50]),
            "summary": summary,
            "data": {
                "top_plans": [
                    {
                        "score": p["score"],
                        "strategy": p["strategy"],
                        "room_count": len(p["plan"].rooms),
                        "total_area": p["plan"].total_area,
                    }
                    for p in top_5
                ],
                "stats": {
                    "total_tested": iteration_count,
                    "avg_score": round(avg_score, 1),
                    "max_score": round(max_score, 1),
                    "min_score": round(min_score, 1),
                    "above_60": len([s for s in scores if s > 60]),
                    "above_70": len([s for s in scores if s > 70]),
                },
            },
        }


def _get_room_program(apt_type: str, target_area: float) -> list[dict]:
    """Daire tipine göre oda programı oluşturur."""
    programs = {
        "1+1": [
            ("Salon", "salon", 0.35), ("Yatak Odası", "yatak_odasi", 0.22),
            ("Mutfak", "mutfak", 0.15), ("Banyo", "banyo", 0.10),
            ("Antre", "antre", 0.08), ("Balkon", "balkon", 0.10),
        ],
        "2+1": [
            ("Salon", "salon", 0.27), ("Yatak Odası 1", "yatak_odasi", 0.17),
            ("Yatak Odası 2", "yatak_odasi", 0.14), ("Mutfak", "mutfak", 0.12),
            ("Banyo", "banyo", 0.07), ("WC", "wc", 0.03),
            ("Antre", "antre", 0.06), ("Koridor", "koridor", 0.05),
            ("Balkon", "balkon", 0.07),
        ],
        "3+1": [
            ("Salon", "salon", 0.24), ("Yatak Odası 1", "yatak_odasi", 0.14),
            ("Yatak Odası 2", "yatak_odasi", 0.12), ("Yatak Odası 3", "yatak_odasi", 0.10),
            ("Mutfak", "mutfak", 0.10), ("Banyo", "banyo", 0.06),
            ("WC", "wc", 0.03), ("Antre", "antre", 0.05),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.06),
            ("Balkon 2", "balkon", 0.04),
        ],
        "4+1": [
            ("Salon", "salon", 0.22), ("Yatak Odası 1", "yatak_odasi", 0.12),
            ("Yatak Odası 2", "yatak_odasi", 0.10), ("Yatak Odası 3", "yatak_odasi", 0.09),
            ("Yatak Odası 4", "yatak_odasi", 0.08), ("Mutfak", "mutfak", 0.09),
            ("Banyo 1", "banyo", 0.05), ("Banyo 2", "banyo", 0.04),
            ("WC", "wc", 0.02), ("Antre", "antre", 0.04),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.05),
            ("Balkon 2", "balkon", 0.03),
        ],
    }

    room_defs = programs.get(apt_type, programs["3+1"])
    return [
        {"isim": name, "tip": tip, "m2": round(target_area * ratio, 1)}
        for name, tip, ratio in room_defs
    ]


def _generate_variant(
    room_program, bw, bh, ox, oy, strategy, sun_dir
) -> FloorPlan:
    """Bir plan varyasyonu üretir (farklı strateji)."""
    rooms = []
    random.seed()  # Her iterasyonda farklı

    # Strateji bazlı randomizasyon
    noise = lambda: random.uniform(-0.3, 0.3)

    if strategy == 0:
        # Strateji 0: Üst-alt bölme (salon üstte)
        rooms = _layout_top_bottom(room_program, bw, bh, ox, oy, sun_dir, noise)
    elif strategy == 1:
        # Strateji 1: Sol-sağ bölme (koridor ortada)
        rooms = _layout_left_right(room_program, bw, bh, ox, oy, sun_dir, noise)
    elif strategy == 2:
        # Strateji 2: L-şekilli salon
        rooms = _layout_l_shape(room_program, bw, bh, ox, oy, sun_dir, noise)
    elif strategy == 3:
        # Strateji 3: Islak hacimler merkezde
        rooms = _layout_wet_center(room_program, bw, bh, ox, oy, sun_dir, noise)
    else:
        # Strateji 4: Tamamen rastgele (mutasyon)
        rooms = _layout_random(room_program, bw, bh, ox, oy, noise)

    total = sum(r.area for r in rooms) if rooms else 0
    return FloorPlan(rooms=rooms, total_area=total, apartment_type="")


def _layout_top_bottom(rooms_def, bw, bh, ox, oy, sun, noise):
    """Salon güneyde (altta), yatak odaları kuzeyde (üstte)."""
    rooms = []
    top_h = bh * 0.45
    bot_h = bh * 0.55
    x_cur = ox

    # Alt sıra: salon, mutfak, balkon
    for rd in rooms_def:
        if rd["tip"] in ("salon", "mutfak", "balkon"):
            w, h = calculate_ideal_dimensions(rd["tip"], rd["m2"])
            w = min(w + noise(), bw - (x_cur - ox))
            h = min(rd["m2"] / max(w, 1), bot_h)
            if w > 0.5 and h > 0.5 and x_cur + w <= ox + bw + 0.5:
                is_ext = x_cur <= ox + 0.1 or x_cur + w >= ox + bw - 0.1
                rooms.append(PlanRoom(
                    name=rd["isim"], room_type=rd["tip"],
                    x=round(x_cur, 2), y=round(oy, 2),
                    width=round(w, 2), height=round(h, 2),
                    has_exterior_wall=is_ext or True,
                    facing_direction="south",
                ))
                x_cur += w + 0.05

    # Üst sıra: yatak odaları, banyo, wc
    x_cur = ox
    for rd in rooms_def:
        if rd["tip"] in ("yatak_odasi", "banyo", "wc", "antre", "koridor"):
            w, h = calculate_ideal_dimensions(rd["tip"], rd["m2"])
            w = min(w + noise(), bw - (x_cur - ox))
            h = min(rd["m2"] / max(w, 1), top_h)
            if w > 0.5 and h > 0.5 and x_cur + w <= ox + bw + 0.5:
                rooms.append(PlanRoom(
                    name=rd["isim"], room_type=rd["tip"],
                    x=round(x_cur, 2), y=round(oy + bot_h, 2),
                    width=round(w, 2), height=round(h, 2),
                    has_exterior_wall=rd["tip"] == "yatak_odasi",
                    facing_direction="north",
                ))
                x_cur += w + 0.05

    return rooms


def _layout_left_right(rooms_def, bw, bh, ox, oy, sun, noise):
    """Sol ve sağ bölme — koridor ortada."""
    rooms = []
    corr_w = 1.2
    half_w = (bw - corr_w) / 2
    y_left, y_right = oy, oy

    # Koridor
    rooms.append(PlanRoom(
        name="Koridor", room_type="koridor",
        x=round(ox + half_w, 2), y=round(oy, 2),
        width=round(corr_w, 2), height=round(bh, 2),
        has_exterior_wall=False,
    ))

    for rd in rooms_def:
        if rd["tip"] == "koridor":
            continue
        m2 = rd["m2"] * (1 + noise() * 0.1)
        w = min(half_w, max(2.0, math.sqrt(m2 * 1.3)))
        h = m2 / max(w, 1)

        # Sol veya sağa yerleştir (dönüşümlü + rastgele)
        if y_left <= y_right and y_left + h <= oy + bh:
            rooms.append(PlanRoom(
                name=rd["isim"], room_type=rd["tip"],
                x=round(ox, 2), y=round(y_left, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=True, facing_direction="west",
            ))
            y_left += h + 0.05
        elif y_right + h <= oy + bh:
            rooms.append(PlanRoom(
                name=rd["isim"], room_type=rd["tip"],
                x=round(ox + half_w + corr_w, 2), y=round(y_right, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=True, facing_direction="east",
            ))
            y_right += h + 0.05

    return rooms


def _layout_l_shape(rooms_def, bw, bh, ox, oy, sun, noise):
    """L-şekilli salon — salon iki duvarı kaplar."""
    rooms = []
    # Salon L-şekilli: alt kenarın %60'ı + sol kenarın %40'ı
    salon = next((r for r in rooms_def if r["tip"] == "salon"), None)
    if salon:
        sw = bw * 0.6
        sh = bh * 0.4
        rooms.append(PlanRoom(
            name="Salon", room_type="salon",
            x=round(ox, 2), y=round(oy, 2),
            width=round(sw, 2), height=round(sh, 2),
            has_exterior_wall=True, facing_direction="south",
        ))

    # Diğer odalar sağ üstte
    x_cur = ox + bw * 0.6
    y_cur = oy
    for rd in rooms_def:
        if rd["tip"] == "salon":
            continue
        m2 = rd["m2"] * (1 + noise() * 0.1)
        avail_w = bw - (x_cur - ox)
        w = min(avail_w, max(2.0, math.sqrt(m2)))
        h = m2 / max(w, 1)
        if y_cur + h > oy + bh:
            x_cur = ox
            y_cur = oy + bh * 0.4
            avail_w = bw * 0.6
            w = min(avail_w, max(2.0, math.sqrt(m2)))
            h = m2 / max(w, 1)
        if y_cur + h <= oy + bh + 0.5:
            rooms.append(PlanRoom(
                name=rd["isim"], room_type=rd["tip"],
                x=round(x_cur, 2), y=round(y_cur, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=x_cur + w >= ox + bw - 0.5,
            ))
            y_cur += h + 0.05

    return rooms


def _layout_wet_center(rooms_def, bw, bh, ox, oy, sun, noise):
    """Islak hacimler merkezde — kuru odalar çevrede."""
    rooms = []
    wet_types = {"banyo", "wc", "mutfak"}
    center_x = ox + bw * 0.35
    center_y = oy + bh * 0.35

    # Islak hacimler merkeze
    wx, wy = center_x, center_y
    for rd in rooms_def:
        if rd["tip"] in wet_types:
            m2 = rd["m2"]
            w = max(1.5, math.sqrt(m2))
            h = m2 / w
            rooms.append(PlanRoom(
                name=rd["isim"], room_type=rd["tip"],
                x=round(wx, 2), y=round(wy, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=False,
            ))
            wx += w + 0.1

    # Kuru odalar çevrede
    x_cur, y_cur = ox, oy
    for rd in rooms_def:
        if rd["tip"] not in wet_types:
            m2 = rd["m2"] * (1 + noise() * 0.1)
            w = min(bw * 0.5, max(2.0, math.sqrt(m2 * 1.2)))
            h = m2 / max(w, 1)
            if x_cur + w > ox + bw:
                x_cur = ox
                y_cur += bh * 0.35
            if y_cur + h <= oy + bh + 0.5:
                rooms.append(PlanRoom(
                    name=rd["isim"], room_type=rd["tip"],
                    x=round(x_cur, 2), y=round(y_cur, 2),
                    width=round(w, 2), height=round(h, 2),
                    has_exterior_wall=True,
                ))
                x_cur += w + 0.1

    return rooms


def _layout_random(rooms_def, bw, bh, ox, oy, noise):
    """Tamamen rastgele yerleştirme (mutasyon amaçlı)."""
    rooms = []
    shuffled = list(rooms_def)
    random.shuffle(shuffled)

    x_cur, y_cur = ox, oy
    row_h = 0
    for rd in shuffled:
        m2 = rd["m2"] * random.uniform(0.85, 1.15)
        w = max(1.5, math.sqrt(m2) * random.uniform(0.8, 1.4))
        h = m2 / max(w, 1)

        if x_cur + w > ox + bw:
            x_cur = ox
            y_cur += row_h + 0.05
            row_h = 0

        if y_cur + h <= oy + bh:
            rooms.append(PlanRoom(
                name=rd["isim"], room_type=rd["tip"],
                x=round(x_cur, 2), y=round(y_cur, 2),
                width=round(w, 2), height=round(h, 2),
                has_exterior_wall=random.random() > 0.4,
            ))
            x_cur += w + 0.05
            row_h = max(row_h, h)

    return rooms
