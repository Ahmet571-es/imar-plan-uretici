"""
Plan Kalite Puanlama — Veri seti kurallarına göre 100 puan üzerinden değerlendirme.
"""

import math
from dataclasses import dataclass, field
from dataset.dataset_rules import (
    ROOM_SIZE_STATS,
    ROOM_ASPECT_RATIOS,
    ADJACENCY_PROBABILITY,
    ROOM_EXTERIOR_WALL_PRIORITY,
    WET_AREA_CLUSTERING,
    CIRCULATION_STATS,
    SCORING_WEIGHTS,
    get_adjacency_score,
    is_wet_area,
)


@dataclass
class PlanRoom:
    """Plan içindeki bir oda."""
    name: str
    room_type: str
    x: float
    y: float
    width: float
    height: float
    has_exterior_wall: bool = False
    facing_direction: str = ""  # north, south, east, west
    doors: list = field(default_factory=list)
    windows: list = field(default_factory=list)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        """Genişlik / uzunluk oranı (her zaman ≤ 1)."""
        short = min(self.width, self.height)
        long = max(self.width, self.height)
        return short / long if long > 0 else 0

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class FloorPlan:
    """Bir dairenin kat planı."""
    rooms: list[PlanRoom] = field(default_factory=list)
    total_area: float = 0.0
    apartment_type: str = "3+1"

    @property
    def circulation_area(self) -> float:
        """Sirkülasyon alanı (koridor + antre)."""
        return sum(r.area for r in self.rooms if r.room_type in ("koridor", "antre"))

    def get_rooms_by_type(self, room_type: str) -> list[PlanRoom]:
        return [r for r in self.rooms if r.room_type == room_type]

    def are_adjacent(self, room1: PlanRoom, room2: PlanRoom, threshold: float = 1.5) -> bool:
        """İki odanın bitişik olup olmadığını kontrol eder.

        Tolerans 1.5m — duvar kalınlığı, koridor geçişi ve küçük boşlukları kapsar.
        Minimum örtüşme eşiği 0.1m — köşeden temas da yeterli sayılır.
        Merkez-merkez mesafesi de kontrol edilir (küçük odalar için).
        """
        r1_right = room1.x + room1.width
        r1_top = room1.y + room1.height
        r2_right = room2.x + room2.width
        r2_top = room2.y + room2.height

        # Yatay veya dikey olarak örtüşen kenar uzunluğu
        h_overlap = max(0, min(r1_right, r2_right) - max(room1.x, room2.x))
        v_overlap = max(0, min(r1_top, r2_top) - max(room1.y, room2.y))

        # Yatay bitişiklik (yan yana) — kenarlar arası mesafe
        h_gap = min(abs(r1_right - room2.x), abs(r2_right - room1.x))
        # Dikey bitişiklik (üst üste) — kenarlar arası mesafe
        v_gap = min(abs(r1_top - room2.y), abs(r2_top - room1.y))

        # Düşük örtüşme eşiği — küçük temas bile yeterli
        min_overlap = 0.1

        if h_gap <= threshold and v_overlap > min_overlap:
            return True
        if v_gap <= threshold and h_overlap > min_overlap:
            return True

        # Merkez-merkez mesafesi kontrolü — yakın odalar bitişik sayılır
        cx1, cy1 = room1.center
        cx2, cy2 = room2.center
        center_dist = math.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
        # Oda boyutlarının yarısı toplamı + tolerans
        boyut_toplami = (max(room1.width, room1.height) + max(room2.width, room2.height)) / 2
        if center_dist <= boyut_toplami + 1.0:
            return True

        return False


@dataclass
class ScoreBreakdown:
    """Puan dağılımı."""
    room_size: float = 0.0
    aspect_ratio: float = 0.0
    adjacency: float = 0.0
    exterior_wall: float = 0.0
    wet_area: float = 0.0
    circulation: float = 0.0
    sun_optimization: float = 0.0
    structural_grid: float = 0.0
    code_compliance: float = 0.0
    pencere_zemin_orani: float = 0.0
    islak_hacim_mesafesi: float = 0.0
    total: float = 0.0
    details: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "Oda Boyut Uyumu": f"{self.room_size:.1f}",
            "En-Boy Oranı": f"{self.aspect_ratio:.1f}",
            "Bitişiklik Uyumu": f"{self.adjacency:.1f}",
            "Dış Cephe Erişimi": f"{self.exterior_wall:.1f}",
            "Islak Hacim Gruplaması": f"{self.wet_area:.1f}",
            "Sirkülasyon Verimliliği": f"{self.circulation:.1f}",
            "Güneş Optimizasyonu": f"{self.sun_optimization:.1f}",
            "Yapısal Grid": f"{self.structural_grid:.1f}",
            "Yönetmelik Uyumu": f"{self.code_compliance:.1f}",
            "Pencere/Zemin Oranı": f"{self.pencere_zemin_orani:.1f}",
            "Islak Hacim Mesafesi": f"{self.islak_hacim_mesafesi:.1f}",
            "TOPLAM": f"{self.total:.1f}/100",
        }


def score_plan(
    plan: FloorPlan,
    sun_best_direction: str = "south",
    violations: list | None = None,
) -> ScoreBreakdown:
    """Kat planını 100 puan üzerinden değerlendirir.

    Args:
        plan: FloorPlan nesnesi.
        sun_best_direction: En iyi güneş yönü.
        violations: Yönetmelik ihlalleri listesi.

    Returns:
        ScoreBreakdown nesnesi.
    """
    score = ScoreBreakdown()
    w = SCORING_WEIGHTS

    # ── 1. Oda Boyut Uyumu (veri setine göre) ──
    size_score = 0.0
    size_max = 0.0
    for room in plan.rooms:
        stats = ROOM_SIZE_STATS.get(room.room_type)
        if stats is None:
            continue
        size_max += 1.0
        if stats["min"] <= room.area <= stats["max"]:
            # Normal aralıkta — mesafeye göre puan (daha yumuşak ceza)
            distance = abs(room.area - stats["avg"]) / (stats["std"] + 1e-6)
            room_score = max(0, 1.0 - distance * 0.12)
            size_score += room_score
            score.details.append(f"✅ {room.name}: {room.area:.1f}m² (ort: {stats['avg']})")
        elif (stats["min"] * 0.7 <= room.area <= stats["max"] * 1.3):
            # Aralık dışı ama kabul edilebilir — kısmi puan
            size_score += 0.4
            score.details.append(f"⚠️ {room.name}: {room.area:.1f}m² aralık dışı [{stats['min']}-{stats['max']}] (kısmi puan)")
        else:
            score.details.append(f"⚠️ {room.name}: {room.area:.1f}m² aralık dışı [{stats['min']}-{stats['max']}]")

    score.room_size = (size_score / max(size_max, 1)) * 100 * w["room_size_compliance"]

    # ── 2. En-Boy Oranı Uyumu ──
    ar_score = 0.0
    ar_max = 0.0
    for room in plan.rooms:
        ratios = ROOM_ASPECT_RATIOS.get(room.room_type)
        if ratios is None:
            continue
        ar_max += 1.0
        if ratios["min"] <= room.aspect_ratio <= ratios["max"]:
            diff = abs(room.aspect_ratio - ratios["ideal"])
            room_ar = max(0, 1.0 - diff / 0.3)
            ar_score += room_ar

    score.aspect_ratio = (ar_score / max(ar_max, 1)) * 100 * w["aspect_ratio_compliance"]

    # ── 3. Bitişiklik Uyumu ──
    adj_score = 0.0
    adj_max = 0.0
    for (r1_type, r2_type), probability in ADJACENCY_PROBABILITY.items():
        rooms_r1 = plan.get_rooms_by_type(r1_type)
        rooms_r2 = plan.get_rooms_by_type(r2_type)
        if not rooms_r1 or not rooms_r2:
            continue
        # Düşük olasılıklı çiftleri de değerlendir (eşik 0.15'e düşürüldü)
        if probability < 0.15:
            continue
        adj_max += probability  # Olasılığa göre ağırlıklı değerlendirme
        # Herhangi bir r1-r2 çifti bitişik mi?
        is_adj = any(
            plan.are_adjacent(r1, r2)
            for r1 in rooms_r1
            for r2 in rooms_r2
        )
        if is_adj:
            # Bitişik — olasılığa göre puan ver
            adj_score += probability
        elif probability > 0.7:
            # Kritik bitişiklik eksik — küçük ceza (azaltıldı)
            adj_score -= 0.05
            score.details.append(f"⚠️ {r1_type}↔{r2_type} bitişik değil (olasılık: {probability:.0%})")

    score.adjacency = max(0, (adj_score / max(adj_max, 0.1))) * 100 * w["adjacency_compliance"]

    # ── 4. Dış Cephe Erişimi ──
    ext_score = 0.0
    ext_max = 0.0
    for room in plan.rooms:
        priority = ROOM_EXTERIOR_WALL_PRIORITY.get(room.room_type, 7)
        if priority <= 3:  # Dış cephe gereken odalar
            ext_max += 1.0
            if room.has_exterior_wall:
                ext_score += (6 - priority) / 5.0
            else:
                score.details.append(f"⚠️ {room.name} dış cepheye bakmalı (öncelik: {priority})")

    score.exterior_wall = (ext_score / max(ext_max, 1)) * 100 * w["exterior_wall_access"]

    # ── 5. Islak Hacim Gruplaması ──
    wet_rooms = [r for r in plan.rooms if is_wet_area(r.room_type)]
    if len(wet_rooms) >= 2:
        max_dist = 0.0
        for i, wr1 in enumerate(wet_rooms):
            for wr2 in wet_rooms[i+1:]:
                dist = math.sqrt(
                    (wr1.center[0] - wr2.center[0])**2 +
                    (wr1.center[1] - wr2.center[1])**2
                )
                max_dist = max(max_dist, dist)

        limit = WET_AREA_CLUSTERING["max_distance_between_wet_areas"]
        if max_dist <= limit:
            score.wet_area = 100 * w["wet_area_clustering"]
        elif max_dist <= limit * 2:
            score.wet_area = 60 * w["wet_area_clustering"]
        else:
            score.wet_area = 20 * w["wet_area_clustering"]
            score.details.append(f"⚠️ Islak hacimler arası mesafe: {max_dist:.1f}m (max {limit}m önerilir)")
    else:
        score.wet_area = 100 * w["wet_area_clustering"]

    # ── 6. Sirkülasyon Verimliliği ──
    if plan.total_area > 0:
        circ_ratio = plan.circulation_area / plan.total_area
        stats = CIRCULATION_STATS
        if stats["min_ratio"] <= circ_ratio <= stats["ideal_ratio"]:
            score.circulation = 100 * w["circulation_efficiency"]
        elif circ_ratio < stats["min_ratio"]:
            score.circulation = 40 * w["circulation_efficiency"]
            score.details.append(f"⚠️ Sirkülasyon oranı düşük: {circ_ratio:.0%} (min {stats['min_ratio']:.0%})")
        elif circ_ratio <= stats["max_ratio"]:
            score.circulation = 70 * w["circulation_efficiency"]
        else:
            score.circulation = 30 * w["circulation_efficiency"]
            score.details.append(f"⚠️ Sirkülasyon oranı yüksek: {circ_ratio:.0%} (max {stats['max_ratio']:.0%})")

    # ── 7. Güneş Optimizasyonu ──
    salon_rooms = plan.get_rooms_by_type("salon")
    balkon_rooms = plan.get_rooms_by_type("balkon")
    sun_score = 0.0
    if salon_rooms and any(r.facing_direction == sun_best_direction for r in salon_rooms):
        sun_score += 50
    if balkon_rooms and any(r.facing_direction == sun_best_direction for r in balkon_rooms):
        sun_score += 50
    score.sun_optimization = sun_score * w["sun_optimization"] / 100 * 100

    # ── 8. Yapısal Grid ──
    # Oda duvarlarının yapısal grid hatlarına hizalanmasını değerlendir
    # Geniş aralık: 1.5-8.0m — küçük odalar (wc, banyo) ve büyük odalar (salon) dahil
    grid_score = 0.0
    grid_max = 0.0
    for room in plan.rooms:
        if room.room_type in ("koridor", "antre"):
            continue
        grid_max += 1.0
        # Oda tipine göre kabul edilebilir boyut aralıkları
        if room.room_type in ("wc", "banyo"):
            # Islak hacimler daha küçük olabilir
            w_ok = 1.2 <= room.width <= 5.0
            h_ok = 1.2 <= room.height <= 5.0
        elif room.room_type == "balkon":
            # Balkon dar olabilir
            w_ok = 1.0 <= room.width <= 6.0
            h_ok = 1.0 <= room.height <= 6.0
        else:
            # Standart odalar — geniş aralık
            w_ok = 2.5 <= room.width <= 8.0
            h_ok = 2.5 <= room.height <= 8.0
        if w_ok and h_ok:
            grid_score += 1.0
        elif w_ok or h_ok:
            grid_score += 0.7
        else:
            grid_score += 0.3
    grid_puan = (grid_score / max(grid_max, 1)) * 100
    score.structural_grid = grid_puan * w["structural_grid"]

    # ── 9. Yönetmelik Uyumu ──
    if violations is None:
        violations = []
    viol_penalty = len(violations) * 20
    score.code_compliance = max(0, 100 - viol_penalty) * w["code_compliance"]

    # ── 10. Pencere/Zemin Oranı ──
    # Türk yapı yönetmeliği: pencere alanı / zemin alanı >= 1/8
    # WC ve koridor hariç her oda pencere almalıdır
    pzo_score = 0.0
    pzo_max = 0.0
    pencere_haric_tipler = ("wc", "koridor", "antre")
    for room in plan.rooms:
        if room.room_type in pencere_haric_tipler:
            continue
        pzo_max += 1.0
        if not room.windows:
            # Penceresi olmayan oda — puan kaybı
            score.details.append(
                f"⚠️ {room.name}: pencere yok (yönetmelik ihlali)"
            )
            continue

        # Toplam pencere alanı tahmini (pencere genişliği × standart yükseklik 1.2m)
        toplam_pencere_alan = sum(
            w.get("width", 0) * 1.2 for w in room.windows
        )
        oran = toplam_pencere_alan / room.area if room.area > 0 else 0
        if oran >= 1 / 8:
            pzo_score += 1.0
        elif oran >= 1 / 12:
            pzo_score += 0.5
            score.details.append(
                f"⚠️ {room.name}: pencere/zemin oranı düşük ({oran:.2f}, min 1/8)"
            )
        else:
            score.details.append(
                f"⚠️ {room.name}: pencere/zemin oranı yetersiz ({oran:.2f}, min 1/8)"
            )

    # Pencere/zemin oranı ağırlığı — toplam puanın %3'ü
    pzo_agirlik = 0.03
    score.pencere_zemin_orani = (
        (pzo_score / max(pzo_max, 1)) * 100 * pzo_agirlik
    )

    # ── 11. Islak Hacim Mesafesi ──
    # Islak hacimler arası merkez-merkez mesafe 5m'yi aşarsa puan kaybı
    ihm_agirlik = 0.02  # Toplam puanın %2'si
    wet_rooms_all = [r for r in plan.rooms if is_wet_area(r.room_type)]
    if len(wet_rooms_all) >= 2:
        max_wet_dist = 0.0
        for i, wr1 in enumerate(wet_rooms_all):
            for wr2 in wet_rooms_all[i + 1:]:
                dist = math.sqrt(
                    (wr1.center[0] - wr2.center[0]) ** 2 +
                    (wr1.center[1] - wr2.center[1]) ** 2
                )
                max_wet_dist = max(max_wet_dist, dist)

        if max_wet_dist <= 5.0:
            score.islak_hacim_mesafesi = 100 * ihm_agirlik
        elif max_wet_dist <= 8.0:
            # Kademeli puan kaybı
            kayip_orani = (max_wet_dist - 5.0) / 3.0
            score.islak_hacim_mesafesi = max(0, (1.0 - kayip_orani)) * 100 * ihm_agirlik
            score.details.append(
                f"⚠️ Islak hacimler arası mesafe: {max_wet_dist:.1f}m (max 5m önerilir)"
            )
        else:
            score.islak_hacim_mesafesi = 0.0
            score.details.append(
                f"⚠️ Islak hacimler arası mesafe çok fazla: {max_wet_dist:.1f}m (max 5m)"
            )
    else:
        score.islak_hacim_mesafesi = 100 * ihm_agirlik

    # ── TOPLAM ──
    score.total = (
        score.room_size +
        score.aspect_ratio +
        score.adjacency +
        score.exterior_wall +
        score.wet_area +
        score.circulation +
        score.sun_optimization +
        score.structural_grid +
        score.code_compliance +
        score.pencere_zemin_orani +
        score.islak_hacim_mesafesi
    )

    return score
