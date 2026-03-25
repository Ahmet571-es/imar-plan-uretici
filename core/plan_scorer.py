"""
Plan Kalite Puanlama — Veri seti kurallarına göre 100 puan üzerinden değerlendirme.

Derinleştirilmiş puanlama kriterleri:
- Oda boyut uyumu (veri seti istatistikleri ile)
- En-boy oranı uyumu (fonksiyonel minimum boyutlar)
- Bitişiklik uyumu (tüm oda çiftleri için)
- Dış cephe erişimi (yön bazlı ağırlıklı)
- Islak hacim gruplaması (tesisat mesafesi)
- Sirkülasyon verimliliği (oran + erişilebilirlik)
- Güneş optimizasyonu (oda bazlı yön analizi)
- Yapısal grid uyumu (aks aralığı kontrolü)
- Yönetmelik uyumu (ihlal sayısı + ağırlık)
- Mahremiyet analizi (sessiz/gürültülü oda ayrımı)
- Fonksiyonel bölge analizi (ıslak/kuru/yaşam ayrımı)
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
    STRUCTURAL_GRID_RULES,
    ROOM_PLACEMENT_RULES,
    get_adjacency_score,
    is_wet_area,
)


# Gürültü sınıflandırması — mahremiyet analizi için
GURULTU_SINIFI = {
    "salon": "orta",
    "yatak_odasi": "sessiz",
    "mutfak": "gurultulu",
    "banyo": "gurultulu",
    "wc": "gurultulu",
    "antre": "orta",
    "koridor": "orta",
    "balkon": "orta",
}

# Fonksiyonel bölge sınıflandırması
FONKSIYONEL_BOLGE = {
    "salon": "yasam",
    "yatak_odasi": "ozel",
    "mutfak": "servis",
    "banyo": "islak",
    "wc": "islak",
    "antre": "gecis",
    "koridor": "gecis",
    "balkon": "dis",
}

# Güneş yönü puan katsayıları (oda tipine göre ideal yön eşleşmesi)
GUNES_YON_PUANI = {
    "salon":       {"south": 1.0, "west": 0.7, "east": 0.7, "north": 0.2},
    "yatak_odasi": {"east": 1.0, "south": 0.8, "west": 0.5, "north": 0.3},
    "mutfak":      {"north": 1.0, "east": 0.8, "west": 0.6, "south": 0.5},
    "balkon":      {"south": 1.0, "west": 0.8, "east": 0.7, "north": 0.1},
    "banyo":       {"north": 1.0, "east": 0.8, "west": 0.8, "south": 0.8},
}


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

    @property
    def min_dimension(self) -> float:
        """En kısa kenar uzunluğu (metre)."""
        return min(self.width, self.height)

    @property
    def perimeter(self) -> float:
        """Oda çevresi (metre)."""
        return 2 * (self.width + self.height)


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

    @property
    def living_area(self) -> float:
        """Yaşam alanı (salon + yatak odaları)."""
        return sum(r.area for r in self.rooms if r.room_type in ("salon", "yatak_odasi"))

    @property
    def service_area(self) -> float:
        """Servis alanı (mutfak + banyo + wc)."""
        return sum(r.area for r in self.rooms if r.room_type in ("mutfak", "banyo", "wc"))

    def get_rooms_by_type(self, room_type: str) -> list[PlanRoom]:
        return [r for r in self.rooms if r.room_type == room_type]

    def are_adjacent(self, room1: PlanRoom, room2: PlanRoom, threshold: float = 0.5) -> bool:
        """İki odanın bitişik olup olmadığını kontrol eder."""
        r1_right = room1.x + room1.width
        r1_top = room1.y + room1.height
        r2_right = room2.x + room2.width
        r2_top = room2.y + room2.height

        h_overlap = max(0, min(r1_right, r2_right) - max(room1.x, room2.x))
        v_overlap = max(0, min(r1_top, r2_top) - max(room1.y, room2.y))

        h_gap = min(abs(r1_right - room2.x), abs(r2_right - room1.x))
        v_gap = min(abs(r1_top - room2.y), abs(r2_top - room1.y))

        if h_gap <= threshold and v_overlap > 0.5:
            return True
        if v_gap <= threshold and h_overlap > 0.5:
            return True
        return False

    def distance_between(self, room1: PlanRoom, room2: PlanRoom) -> float:
        """İki oda merkezi arası mesafe."""
        c1 = room1.center
        c2 = room2.center
        return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)


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
    total: float = 0.0
    details: list = field(default_factory=list)

    # Derinleştirilmiş analiz verileri
    mahremiyet_puani: float = 0.0
    fonksiyonel_bolge_puani: float = 0.0
    min_boyut_uyumu: float = 0.0
    gunes_detay: dict = field(default_factory=dict)
    alan_dagilim_analizi: dict = field(default_factory=dict)
    genel_degerlendirme: str = ""

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
            "TOPLAM": f"{self.total:.1f}/100",
        }

    def to_detailed_dict(self) -> dict:
        """Derinleştirilmiş puan kartı."""
        d = self.to_dict()
        d["Mahremiyet Puanı"] = f"{self.mahremiyet_puani:.0f}/100"
        d["Fonksiyonel Bölge"] = f"{self.fonksiyonel_bolge_puani:.0f}/100"
        d["Min. Boyut Uyumu"] = f"{self.min_boyut_uyumu:.0f}/100"
        d["Genel Değerlendirme"] = self.genel_degerlendirme
        return d


def score_plan(
    plan: FloorPlan,
    sun_best_direction: str = "south",
    violations: list | None = None,
) -> ScoreBreakdown:
    """Kat planını 100 puan üzerinden değerlendirir.

    Derinleştirilmiş puanlama: 9 temel kriter + 3 ek analiz.

    Args:
        plan: FloorPlan nesnesi.
        sun_best_direction: En iyi güneş yönü.
        violations: Yönetmelik ihlalleri listesi.

    Returns:
        ScoreBreakdown nesnesi.
    """
    score = ScoreBreakdown()
    w = SCORING_WEIGHTS

    if not plan.rooms:
        score.genel_degerlendirme = "Boş plan — puanlama yapılamadı"
        return score

    # ── 1. Oda Boyut Uyumu (veri setine göre) ──
    size_score = 0.0
    size_max = 0.0
    for room in plan.rooms:
        stats = ROOM_SIZE_STATS.get(room.room_type)
        if stats is None:
            continue
        size_max += 1.0
        if stats["min"] <= room.area <= stats["max"]:
            distance = abs(room.area - stats["avg"]) / (stats["std"] + 1e-6)
            room_score = max(0, 1.0 - distance * 0.2)
            size_score += room_score
            # Türkiye ortalamasına yakınlık detayı
            tr_diff = abs(room.area - stats.get("turkiye_avg", stats["avg"]))
            if tr_diff < stats["std"]:
                score.details.append(f"✅ {room.name}: {room.area:.1f}m² (TR ort: {stats.get('turkiye_avg', stats['avg'])}m²)")
            else:
                score.details.append(f"ℹ️ {room.name}: {room.area:.1f}m² (ort: {stats['avg']}, TR ort: {stats.get('turkiye_avg', stats['avg'])})")
        else:
            score.details.append(f"⚠️ {room.name}: {room.area:.1f}m² aralık dışı [{stats['min']}-{stats['max']}]")

    score.room_size = (size_score / max(size_max, 1)) * 100 * w["room_size_compliance"]

    # ── 2. En-Boy Oranı + Minimum Boyut Uyumu ──
    ar_score = 0.0
    ar_max = 0.0
    min_dim_ok = 0
    min_dim_total = 0
    MIN_BOYUTLAR = {"salon": 3.0, "yatak_odasi": 2.8, "mutfak": 2.2, "banyo": 1.5, "wc": 0.9, "koridor": 1.1}

    for room in plan.rooms:
        ratios = ROOM_ASPECT_RATIOS.get(room.room_type)
        if ratios is None:
            continue
        ar_max += 1.0
        if ratios["min"] <= room.aspect_ratio <= ratios["max"]:
            diff = abs(room.aspect_ratio - ratios["ideal"])
            room_ar = max(0, 1.0 - diff / 0.3)
            ar_score += room_ar

        # Minimum boyut kontrolü
        min_req = MIN_BOYUTLAR.get(room.room_type)
        if min_req:
            min_dim_total += 1
            if room.min_dimension >= min_req:
                min_dim_ok += 1
            else:
                score.details.append(f"⚠️ {room.name}: kısa kenar {room.min_dimension:.2f}m < min {min_req}m")

    score.aspect_ratio = (ar_score / max(ar_max, 1)) * 100 * w["aspect_ratio_compliance"]
    score.min_boyut_uyumu = (min_dim_ok / max(min_dim_total, 1)) * 100

    # ── 3. Bitişiklik Uyumu ──
    adj_score = 0.0
    adj_max = 0.0
    for (r1_type, r2_type), probability in ADJACENCY_PROBABILITY.items():
        rooms_r1 = plan.get_rooms_by_type(r1_type)
        rooms_r2 = plan.get_rooms_by_type(r2_type)
        if not rooms_r1 or not rooms_r2:
            continue
        adj_max += 1.0
        is_adj = any(
            plan.are_adjacent(r1, r2)
            for r1 in rooms_r1
            for r2 in rooms_r2
        )
        if is_adj and probability > 0.5:
            adj_score += probability
        elif not is_adj and probability > 0.7:
            adj_score -= 0.3
            score.details.append(f"⚠️ {r1_type}↔{r2_type} bitişik değil (olasılık: {probability:.0%})")

    score.adjacency = max(0, (adj_score / max(adj_max, 1))) * 100 * w["adjacency_compliance"]

    # ── 4. Dış Cephe Erişimi (yön bazlı ağırlıklı) ──
    ext_score = 0.0
    ext_max = 0.0
    for room in plan.rooms:
        priority = ROOM_EXTERIOR_WALL_PRIORITY.get(room.room_type, 7)
        if priority <= 3:
            ext_max += 1.0
            if room.has_exterior_wall:
                # Yön uygunluğuna göre bonus
                yon_bonus = 1.0
                rules = ROOM_PLACEMENT_RULES.get(room.room_type, {})
                preferred_sun = rules.get("sun_preference", "")
                if room.facing_direction == preferred_sun:
                    yon_bonus = 1.3  # %30 bonus ideal yöne bakan odalar için
                ext_score += (6 - priority) / 5.0 * yon_bonus
            else:
                score.details.append(f"⚠️ {room.name} dış cepheye bakmalı (öncelik: {priority})")

    score.exterior_wall = min(100 * w["exterior_wall_access"],
                              (ext_score / max(ext_max, 1)) * 100 * w["exterior_wall_access"])

    # ── 5. Islak Hacim Gruplaması ──
    wet_rooms = [r for r in plan.rooms if is_wet_area(r.room_type)]
    if len(wet_rooms) >= 2:
        max_dist = 0.0
        avg_dist = 0.0
        pair_count = 0
        for i, wr1 in enumerate(wet_rooms):
            for wr2 in wet_rooms[i+1:]:
                dist = math.sqrt(
                    (wr1.center[0] - wr2.center[0])**2 +
                    (wr1.center[1] - wr2.center[1])**2
                )
                max_dist = max(max_dist, dist)
                avg_dist += dist
                pair_count += 1
        avg_dist = avg_dist / max(pair_count, 1)

        limit = WET_AREA_CLUSTERING["max_distance_between_wet_areas"]
        if max_dist <= limit:
            score.wet_area = 100 * w["wet_area_clustering"]
            score.details.append(f"✅ Islak hacimler iyi gruplanmış (maks mesafe: {max_dist:.1f}m)")
        elif max_dist <= limit * 2:
            score.wet_area = 60 * w["wet_area_clustering"]
            score.details.append(f"ℹ️ Islak hacimler kısmen gruplu (maks: {max_dist:.1f}m, ort: {avg_dist:.1f}m)")
        else:
            score.wet_area = 20 * w["wet_area_clustering"]
            score.details.append(f"⚠️ Islak hacimler dağınık: maks {max_dist:.1f}m, ort {avg_dist:.1f}m (max {limit}m önerilir)")
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

    # ── 7. Güneş Optimizasyonu (derinleştirilmiş — oda bazlı) ──
    sun_score = 0.0
    sun_max = 0.0
    gunes_detay = {}
    for room in plan.rooms:
        yon_puanlari = GUNES_YON_PUANI.get(room.room_type)
        if yon_puanlari is None or not room.facing_direction:
            continue
        sun_max += 1.0
        oda_gunes_puan = yon_puanlari.get(room.facing_direction, 0.3)
        sun_score += oda_gunes_puan
        gunes_detay[room.name] = {
            "yon": room.facing_direction,
            "puan": round(oda_gunes_puan * 100),
            "ideal_yon": max(yon_puanlari, key=yon_puanlari.get),
        }

    if sun_max > 0:
        score.sun_optimization = (sun_score / sun_max) * 100 * w["sun_optimization"]
    score.gunes_detay = gunes_detay

    # ── 8. Yapısal Grid Uyumu (derinleştirilmiş) ──
    grid = STRUCTURAL_GRID_RULES
    grid_score = 0
    grid_checks = 0
    for room in plan.rooms:
        if room.room_type in ("balkon", "koridor"):
            continue
        grid_checks += 1
        w_ok = grid["typical_span_min"] <= room.width <= grid["typical_span_max"]
        h_ok = grid["typical_span_min"] <= room.height <= grid["typical_span_max"]
        if w_ok and h_ok:
            grid_score += 1.0
        elif w_ok or h_ok:
            grid_score += 0.5
        else:
            score.details.append(f"⚠️ {room.name}: boyutlar ({room.width:.1f}×{room.height:.1f}m) yapısal grid dışı [{grid['typical_span_min']}-{grid['typical_span_max']}m]")

    score.structural_grid = (grid_score / max(grid_checks, 1)) * 100 * w["structural_grid"]

    # ── 9. Yönetmelik Uyumu ──
    if violations is None:
        violations = []
    viol_penalty = len(violations) * 20
    score.code_compliance = max(0, 100 - viol_penalty) * w["code_compliance"]

    # ══ EK ANALİZLER (puana dahil değil, detay bilgi) ══

    # ── Mahremiyet Analizi ──
    mahremiyet = 100.0
    for room in plan.rooms:
        if GURULTU_SINIFI.get(room.room_type) == "sessiz":
            # Sessiz oda, gürültülü odaya bitişik mi?
            for other in plan.rooms:
                if GURULTU_SINIFI.get(other.room_type) == "gurultulu":
                    if plan.are_adjacent(room, other):
                        mahremiyet -= 15
                        score.details.append(f"⚠️ Mahremiyet: {room.name} (sessiz) ↔ {other.name} (gürültülü) bitişik")
    score.mahremiyet_puani = max(0, mahremiyet)

    # ── Fonksiyonel Bölge Analizi ──
    bolge_gruplanma = 0
    bolge_total = 0
    bolge_map = {}
    for room in plan.rooms:
        bolge = FONKSIYONEL_BOLGE.get(room.room_type, "diger")
        if bolge not in bolge_map:
            bolge_map[bolge] = []
        bolge_map[bolge].append(room)

    # Aynı bölgedeki odalar birbirine yakın mı?
    for bolge, rooms in bolge_map.items():
        if len(rooms) < 2 or bolge == "gecis":
            continue
        for i, r1 in enumerate(rooms):
            for r2 in rooms[i+1:]:
                bolge_total += 1
                if plan.are_adjacent(r1, r2) or plan.distance_between(r1, r2) < 5.0:
                    bolge_gruplanma += 1

    score.fonksiyonel_bolge_puani = (bolge_gruplanma / max(bolge_total, 1)) * 100

    # ── Alan Dağılım Analizi ──
    if plan.total_area > 0:
        score.alan_dagilim_analizi = {
            "yasam_orani": f"{plan.living_area / plan.total_area * 100:.0f}%",
            "servis_orani": f"{plan.service_area / plan.total_area * 100:.0f}%",
            "sirkulasyon_orani": f"{plan.circulation_area / plan.total_area * 100:.0f}%",
            "yasam_alan": f"{plan.living_area:.1f} m²",
            "servis_alan": f"{plan.service_area:.1f} m²",
            "sirkulasyon_alan": f"{plan.circulation_area:.1f} m²",
        }

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
        score.code_compliance
    )

    # ── Genel Değerlendirme ──
    if score.total >= 80:
        score.genel_degerlendirme = "Mükemmel plan — veri seti kurallarına yüksek uyum"
    elif score.total >= 65:
        score.genel_degerlendirme = "İyi plan — küçük iyileştirmelerle mükemmelleştirilebilir"
    elif score.total >= 50:
        score.genel_degerlendirme = "Orta plan — bazı konularda iyileştirme gerekli"
    else:
        score.genel_degerlendirme = "Geliştirilmesi gereken plan — birçok kriter karşılanmıyor"

    return score
