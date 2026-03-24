"""
Ajan Ayarları ve Yapılandırma — Tüm ajan örneklerini ve parametreleri yönetir.
"""

from agents.orchestrator import OrkestatorAjani
from agents.plan_optimizasyon import PlanOptimizasyonAjani
from agents.maliyet_optimizasyon import MaliyetOptimizasyonAjani
from agents.daire_karmasi import DaireKarmasiAjani
from agents.toplu_fizibilite import TopluFizibiliteAjani


def create_agent_system():
    """Tüm ajanları oluşturur ve orkestratöre kaydeder.

    Returns:
        (orkestrator, {ajan_adi: ajan_instance})
    """
    orkestrator = OrkestatorAjani()

    ajanlar = {
        "plan_optimizasyon": PlanOptimizasyonAjani(),
        "maliyet_optimizasyon": MaliyetOptimizasyonAjani(),
        "daire_karmasi": DaireKarmasiAjani(),
        "toplu_fizibilite": TopluFizibiliteAjani(),
    }

    for ajan in ajanlar.values():
        orkestrator.register_agent(ajan)

    return orkestrator, ajanlar


# Varsayılan çalışma parametreleri
DEFAULT_PARAMS = {
    "plan_optimizasyon": {
        "buildable_width": 16.0,
        "buildable_height": 12.0,
        "apartment_type": "3+1",
        "target_area": 120.0,
        "iteration_count": 200,
        "sun_direction": "south",
    },
    "maliyet_optimizasyon": {
        "toplam_insaat_alani": 850.0,
        "il": "Ankara",
        "arsa_maliyeti": 5_000_000,
        "otopark_arac": 8,
        "hedef_satis_m2": 40_000,
    },
    "daire_karmasi": {
        "kat_basi_net_alan": 190.0,
        "kat_sayisi": 4,
        "toplam_insaat_alani": 850.0,
        "il": "Ankara",
        "baz_m2_fiyat": 40_000,
        "arsa_maliyeti": 5_000_000,
    },
    "toplu_fizibilite": {
        "parseller": None,  # None = demo verisi
        "il": "Ankara",
        "m2_satis_fiyati": 40_000,
        "kalite": "orta",
        "daire_tipi": "3+1",
        "daire_per_kat": 2,
    },
}


AJAN_BILGILERI = {
    "plan_optimizasyon": {
        "emoji": "📐",
        "baslik": "Plan Optimizasyon",
        "aciklama": "Yüzlerce plan varyasyonu üretir, puanlar, en iyileri seçer",
        "calisma_suresi": "~30sn (200 iterasyon)",
    },
    "maliyet_optimizasyon": {
        "emoji": "💰",
        "baslik": "Maliyet Optimizasyon",
        "aciklama": "4 yapı sistemi + 3 malzeme paketi karşılaştırır",
        "calisma_suresi": "~5sn",
    },
    "daire_karmasi": {
        "emoji": "🏠",
        "baslik": "Daire Karması",
        "aciklama": "2+1/3+1/4+1 kombinasyonlarını kârlılığa göre optimize eder",
        "calisma_suresi": "~10sn",
    },
    "toplu_fizibilite": {
        "emoji": "📊",
        "baslik": "Toplu Fizibilite",
        "aciklama": "Birden fazla parseli toplu analiz eder, kârlılığa göre sıralar",
        "calisma_suresi": "~15sn (8 parsel)",
    },
    "orkestrator": {
        "emoji": "🧠",
        "baslik": "Orkestratör",
        "aciklama": "Tüm ajan sonuçlarını analiz eder, aksiyonları belirler",
        "calisma_suresi": "~2sn",
    },
}
