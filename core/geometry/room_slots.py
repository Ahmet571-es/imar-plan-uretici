"""
Oda slotları — RoomSlot dataclass ve oda programı oluşturma.
"""

from dataclasses import dataclass, field
from config.room_defaults import MINIMUM_ODA_ALANLARI
from dataset.dataset_rules import ROOM_EXTERIOR_WALL_PRIORITY


# ═══════════════════════════════════════════════════════════════
# VERİ YAPILARI
# ═══════════════════════════════════════════════════════════════

@dataclass
class RoomSlot:
    """Yerleştirme öncesi oda slotu."""
    name: str
    room_type: str
    target_area: float
    min_width: float = 2.0
    priority: int = 5         # Dış cephe önceliği (1=en yüksek)
    is_wet: bool = False
    placed: bool = False
    # Yerleştirme sonrası
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


# ═══════════════════════════════════════════════════════════════
# ODA PROGRAMI
# ═══════════════════════════════════════════════════════════════

def _default_room_program(apt_type: str, target: float,
                           open_plan: bool = False,
                           en_suite: bool = False) -> list[dict]:
    """Daire tipine göre varsayılan oda programı."""
    programs = {
        "1+1": [
            ("Salon", "salon", 0.33), ("Yatak Odası", "yatak_odasi", 0.22),
            ("Mutfak", "mutfak", 0.15), ("Banyo", "banyo", 0.10),
            ("Antre", "antre", 0.08), ("Balkon", "balkon", 0.08),
        ],
        "2+1": [
            ("Salon", "salon", 0.26), ("Yatak Odası 1", "yatak_odasi", 0.16),
            ("Yatak Odası 2", "yatak_odasi", 0.13), ("Mutfak", "mutfak", 0.12),
            ("Banyo", "banyo", 0.07), ("WC", "wc", 0.03),
            ("Antre", "antre", 0.06), ("Koridor", "koridor", 0.06),
            ("Balkon", "balkon", 0.06),
        ],
        "3+1": [
            ("Salon", "salon", 0.23), ("Yatak Odası 1", "yatak_odasi", 0.13),
            ("Yatak Odası 2", "yatak_odasi", 0.11),
            ("Yatak Odası 3", "yatak_odasi", 0.09),
            ("Mutfak", "mutfak", 0.10), ("Banyo", "banyo", 0.055),
            ("WC", "wc", 0.025), ("Antre", "antre", 0.05),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.055),
        ],
        "4+1": [
            ("Salon", "salon", 0.21), ("Yatak Odası 1", "yatak_odasi", 0.11),
            ("Yatak Odası 2", "yatak_odasi", 0.10),
            ("Yatak Odası 3", "yatak_odasi", 0.08),
            ("Yatak Odası 4", "yatak_odasi", 0.08), ("Mutfak", "mutfak", 0.09),
            ("Banyo 1", "banyo", 0.05), ("Banyo 2", "banyo", 0.035),
            ("WC", "wc", 0.025), ("Antre", "antre", 0.04),
            ("Koridor", "koridor", 0.05), ("Balkon", "balkon", 0.05),
        ],
    }
    room_defs = list(programs.get(apt_type, programs["3+1"]))

    # Açık plan salon-mutfak
    if open_plan:
        salon_r = next((r for n, t, r in room_defs if t == "salon"), 0.23)
        mutfak_r = next((r for n, t, r in room_defs if t == "mutfak"), 0.10)
        room_defs = [(n, t, r) for n, t, r in room_defs
                     if t not in ("salon", "mutfak")]
        room_defs.insert(0, ("Salon + Mutfak", "salon_mutfak",
                             salon_r + mutfak_r))

    # En-suite banyo
    if en_suite and apt_type in ("3+1", "4+1"):
        room_defs.append(("Ebeveyn Banyosu", "banyo", 0.04))

    # Toplam oda yüzdelerinin %100'ü aşmadığını doğrula
    toplam_oran = sum(r for _, _, r in room_defs)
    if toplam_oran > 1.0:
        # Oranları normalize et — %100'e sığdır
        room_defs = [(n, t, r / toplam_oran) for n, t, r in room_defs]

    return [{"isim": n, "tip": t, "m2": round(target * r, 1)}
            for n, t, r in room_defs]


def _create_room_slots(room_program: list[dict]) -> list[RoomSlot]:
    """Oda programından slot'lar oluşturur.

    Hedef alan, yönetmelikteki minimum alanın altındaysa otomatik olarak
    minimum alana yükseltilir (3194 sayılı İmar Kanunu).
    """
    slots = []
    wet_types = {"banyo", "wc", "mutfak"}
    for rd in room_program:
        tip = rd.get("tip", "diger")
        if tip == "koridor":
            continue  # Koridor ayrıca oluşturulur

        hedef_alan = rd.get("m2", 10)

        # Minimum alan kontrolü — İmar Kanunu zorunlu alt sınırları
        effective_tip = tip if tip != "salon_mutfak" else "salon_mutfak"
        min_alan = MINIMUM_ODA_ALANLARI.get(effective_tip, 0.0)
        if hedef_alan < min_alan:
            hedef_alan = min_alan

        slots.append(RoomSlot(
            name=rd.get("isim", "Oda"),
            room_type=tip if tip != "salon_mutfak" else "salon",
            target_area=hedef_alan,
            priority=ROOM_EXTERIOR_WALL_PRIORITY.get(
                tip if tip != "salon_mutfak" else "salon", 5),
            is_wet=tip in wet_types,
            min_width=1.5 if tip in ("wc",) else 2.0,
        ))
    return slots
