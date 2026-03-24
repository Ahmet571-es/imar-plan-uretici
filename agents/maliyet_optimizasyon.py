"""
Ajan 6 — Maliyet Optimizasyon: Farklı yapı sistemleri ve malzeme seçeneklerini karşılaştırır.
"""

from agents.base_agent import BaseAgent
from analysis.cost_estimator import hesapla_maliyet


YAPI_SISTEMLERI = {
    "betonarme_karkas": {
        "isim": "Betonarme Karkas",
        "m2_carpan": 1.00,
        "sure_carpan": 1.00,
        "kalite": "Standart",
        "uygun_kat": "1-30",
    },
    "tunel_kalip": {
        "isim": "Tünel Kalıp",
        "m2_carpan": 0.90,
        "sure_carpan": 0.70,
        "kalite": "Yüksek (düzgün yüzey)",
        "uygun_kat": "4-20",
    },
    "celik_yapi": {
        "isim": "Çelik Yapı",
        "m2_carpan": 1.15,
        "sure_carpan": 0.60,
        "kalite": "Yüksek",
        "uygun_kat": "1-50+",
    },
    "prekast": {
        "isim": "Prekast Beton",
        "m2_carpan": 0.95,
        "sure_carpan": 0.55,
        "kalite": "Standart-Yüksek",
        "uygun_kat": "1-15",
    },
}

MALZEME_ALTERNATIFLERI = {
    "dis_cephe": {
        "mantolama_eps": {"isim": "EPS Mantolama", "carpan": 1.00},
        "mantolama_xps": {"isim": "XPS Mantolama", "carpan": 1.15},
        "ventile_cephe": {"isim": "Ventile Cephe", "carpan": 2.20},
        "kompozit_panel": {"isim": "Kompozit Panel", "carpan": 1.80},
    },
    "doseme": {
        "seramik": {"isim": "Seramik", "carpan": 1.00},
        "laminat": {"isim": "Laminat Parke", "carpan": 1.10},
        "parke":   {"isim": "Masif Parke", "carpan": 1.80},
    },
    "mutfak": {
        "mdf":     {"isim": "MDF Mutfak", "carpan": 1.00},
        "akrilik": {"isim": "Akrilik Mutfak", "carpan": 1.40},
        "lake":    {"isim": "Lake Mutfak", "carpan": 1.60},
    },
    "banyo": {
        "standart": {"isim": "Standart", "carpan": 1.00},
        "premium":  {"isim": "Premium", "carpan": 1.70},
    },
}


class MaliyetOptimizasyonAjani(BaseAgent):
    """Farklı yapı sistemi ve malzeme kombinasyonlarını karşılaştırır."""

    def __init__(self):
        super().__init__(
            name="maliyet_optimizasyon",
            description="Yapı sistemi ve malzeme alternatifleri karşılaştırır",
        )

    def execute(
        self,
        toplam_insaat_alani: float = 850.0,
        il: str = "Ankara",
        arsa_maliyeti: float = 5_000_000,
        otopark_arac: int = 8,
        hedef_satis_m2: float = 40_000,
        **kwargs,
    ) -> dict:
        # ── 1. Yapı sistemi karşılaştırması ──
        yapi_sonuclari = []
        for kod, sistem in YAPI_SISTEMLERI.items():
            maliyet = hesapla_maliyet(
                toplam_insaat_alani=toplam_insaat_alani,
                il=il,
                kalite="orta",
                arsa_maliyeti=arsa_maliyeti,
                otopark_arac_sayisi=otopark_arac,
            )
            adjusted_cost = maliyet.toplam_maliyet * sistem["m2_carpan"]
            toplam_gelir = toplam_insaat_alani * 0.78 * hedef_satis_m2  # %78 net oran
            kar = toplam_gelir - adjusted_cost
            kar_marji = (kar / toplam_gelir * 100) if toplam_gelir > 0 else 0

            yapi_sonuclari.append({
                "sistem": sistem["isim"],
                "maliyet": round(adjusted_cost),
                "sure_carpan": sistem["sure_carpan"],
                "kar": round(kar),
                "kar_marji": round(kar_marji, 1),
                "kalite": sistem["kalite"],
            })

        yapi_sonuclari.sort(key=lambda x: x["kar"], reverse=True)
        en_karli = yapi_sonuclari[0]
        en_hizli = min(yapi_sonuclari, key=lambda x: x["sure_carpan"])

        # ── 2. Malzeme kombinasyonları ──
        baz_maliyet = hesapla_maliyet(toplam_insaat_alani, il, "orta", arsa_maliyeti, otopark_arac_sayisi=otopark_arac)

        malzeme_senaryolari = []
        # Ekonomik
        eko_carpan = 1.0
        for kategori, secenekler in MALZEME_ALTERNATIFLERI.items():
            ilk = list(secenekler.values())[0]
            eko_carpan *= 1.0  # en ucuz

        # Premium
        prem_carpan = 1.0
        for kategori, secenekler in MALZEME_ALTERNATIFLERI.items():
            son = list(secenekler.values())[-1]
            prem_carpan *= son["carpan"]

        # İnce inşaat %27 oranında
        ince_oran = 0.27
        eko_maliyet = baz_maliyet.toplam_maliyet * (1 - ince_oran * 0.10)  # %10 tasarruf
        prem_maliyet = baz_maliyet.toplam_maliyet * (1 + ince_oran * 0.35)  # %35 artış

        malzeme_senaryolari = [
            {"senaryo": "Ekonomik Paket", "maliyet": round(eko_maliyet), "aciklama": "En uygun malzemeler"},
            {"senaryo": "Standart Paket", "maliyet": round(baz_maliyet.toplam_maliyet), "aciklama": "Orta segment"},
            {"senaryo": "Premium Paket", "maliyet": round(prem_maliyet), "aciklama": "Üst segment malzemeler"},
        ]

        summary = (
            f"4 yapı sistemi + 3 malzeme paketi analiz edildi. "
            f"En kârlı sistem: {en_karli['sistem']} (%{en_karli['kar_marji']} kâr). "
            f"En hızlı: {en_hizli['sistem']} (süre ×{en_hizli['sure_carpan']:.2f}). "
            f"Maliyet aralığı: {malzeme_senaryolari[0]['maliyet']:,.0f}₺ — {malzeme_senaryolari[-1]['maliyet']:,.0f}₺"
        )

        return {
            "success": True,
            "items_found": len(yapi_sonuclari) + len(malzeme_senaryolari),
            "summary": summary,
            "data": {
                "yapi_sistemleri": yapi_sonuclari,
                "malzeme_senaryolari": malzeme_senaryolari,
                "en_karli_sistem": en_karli,
                "en_hizli_sistem": en_hizli,
            },
        }
