"""
Ajan 7 — Daire Karması Optimizasyon: 2+1/3+1/4+1 oranlarını kârlılığa göre optimize eder.
"""

import itertools
from agents.base_agent import BaseAgent
from analysis.cost_estimator import hesapla_maliyet
from analysis.revenue_estimator import hesapla_gelir
from analysis.feasibility import hesapla_fizibilite


# Daire tipi bazlı ortalama m² fiyat çarpanları (baz fiyata göre)
DAIRE_TIPI_FIYAT_CARPANI = {
    "1+1": 1.10,   # Küçük daireler m²'si biraz pahalı
    "2+1": 1.05,
    "3+1": 1.00,   # Baz
    "4+1": 0.95,   # Büyük daireler m²'si biraz ucuz
    "5+1": 0.90,
}

DAIRE_TIPI_BRUT_ALAN = {
    "1+1": 55, "2+1": 90, "3+1": 125, "4+1": 165, "5+1": 220,
}

# Tahmini satış süresi (ay) — bölge ve tipe göre
SATIS_SURESI_TAHMINI = {
    "1+1": 3,   # Hızlı satılır (yatırımcı talebi)
    "2+1": 4,
    "3+1": 6,
    "4+1": 9,
    "5+1": 12,
}


class DaireKarmasiAjani(BaseAgent):
    """Daire karması kombinasyonlarını kârlılık ve satış hızına göre optimize eder."""

    def __init__(self):
        super().__init__(
            name="daire_karmasi",
            description="En kârlı ve en hızlı satılan daire karması kombinasyonunu bulur",
        )

    def execute(
        self,
        kat_basi_net_alan: float = 190.0,
        kat_sayisi: int = 4,
        toplam_insaat_alani: float = 850.0,
        il: str = "Ankara",
        baz_m2_fiyat: float = 40_000,
        arsa_maliyeti: float = 5_000_000,
        otopark_arac_basi: int = 1,
        daire_tipleri: list[str] | None = None,
        **kwargs,
    ) -> dict:
        if daire_tipleri is None:
            daire_tipleri = ["2+1", "3+1", "4+1"]

        toplam_net = kat_basi_net_alan * kat_sayisi
        senaryolar = []

        # Tüm kombinasyonları üret
        for combo in _generate_combinations(toplam_net, daire_tipleri, max_daire=12):
            daire_sayisi = sum(combo.values())
            if daire_sayisi == 0:
                continue

            # Gelir hesapla
            daire_listesi = []
            daire_no = 1
            for tip, adet in combo.items():
                brut = DAIRE_TIPI_BRUT_ALAN[tip]
                net = brut * 0.78
                m2_fiyat = baz_m2_fiyat * DAIRE_TIPI_FIYAT_CARPANI.get(tip, 1.0)
                for _ in range(adet):
                    kat = (daire_no - 1) // max(1, daire_sayisi // kat_sayisi) + 1
                    daire_listesi.append({
                        "daire_no": daire_no, "kat": min(kat, kat_sayisi),
                        "tip": tip, "net_alan": net,
                    })
                    daire_no += 1

            gelir = hesapla_gelir(daire_listesi, baz_m2_fiyat, kat_sayisi)

            # Maliyet
            otopark = daire_sayisi * otopark_arac_basi
            maliyet = hesapla_maliyet(toplam_insaat_alani, il, "orta", arsa_maliyeti=arsa_maliyeti, otopark_arac_sayisi=otopark)

            # Fizibilite
            fiz = hesapla_fizibilite(gelir.toplam_gelir, maliyet.toplam_maliyet, toplam_insaat_alani * 0.78)

            # Ortalama satış süresi
            toplam_ay = 0
            for tip, adet in combo.items():
                toplam_ay += SATIS_SURESI_TAHMINI.get(tip, 6) * adet
            ort_satis_suresi = toplam_ay / max(daire_sayisi, 1)

            senaryolar.append({
                "kombinasyon": dict(combo),
                "daire_sayisi": daire_sayisi,
                "toplam_gelir": round(gelir.toplam_gelir),
                "toplam_gider": round(maliyet.toplam_maliyet),
                "kar": round(fiz.kar_zarar),
                "kar_marji": round(fiz.kar_marji, 1),
                "roi": round(fiz.roi, 1),
                "ort_satis_suresi_ay": round(ort_satis_suresi, 1),
                "label": " + ".join(f"{v}×{k}" for k, v in combo.items() if v > 0),
            })

        # Sırala
        senaryolar.sort(key=lambda x: x["kar"], reverse=True)

        # En iyi 3 kategori
        en_karli = senaryolar[0] if senaryolar else None
        en_hizli = min(senaryolar, key=lambda x: x["ort_satis_suresi_ay"]) if senaryolar else None
        # Dengeli: kâr marjı × (1 / satış süresi) en yüksek olan
        for s in senaryolar:
            s["dengeli_skor"] = s["kar_marji"] / max(s["ort_satis_suresi_ay"], 1)
        dengeli = max(senaryolar, key=lambda x: x["dengeli_skor"]) if senaryolar else None

        summary = (
            f"{len(senaryolar)} kombinasyon analiz edildi. "
            f"En kârlı: {en_karli['label']} (%{en_karli['kar_marji']} kâr). "
            f"En hızlı satış: {en_hizli['label']} ({en_hizli['ort_satis_suresi_ay']:.0f} ay). "
            f"Dengeli: {dengeli['label']}"
            if en_karli and en_hizli and dengeli else "Kombinasyon bulunamadı"
        )

        return {
            "success": True,
            "items_found": len(senaryolar),
            "summary": summary,
            "data": {
                "tum_senaryolar": senaryolar[:20],  # İlk 20
                "en_karli": en_karli,
                "en_hizli_satis": en_hizli,
                "dengeli": dengeli,
            },
        }


def _generate_combinations(
    toplam_alan: float,
    tipler: list[str],
    max_daire: int = 12,
    tolerans: float = 0.15,
) -> list[dict]:
    """Toplam alana uyan daire kombinasyonlarını üretir."""
    combos = []
    tip_alanlari = {t: DAIRE_TIPI_BRUT_ALAN[t] for t in tipler}

    # Her tip için max adet
    max_adetler = {t: int(toplam_alan / a) + 1 for t, a in tip_alanlari.items()}

    # İteratif kombinasyon üretimi
    ranges = [range(0, min(max_adetler[t], max_daire) + 1) for t in tipler]

    for counts in itertools.product(*ranges):
        combo = dict(zip(tipler, counts))
        toplam = sum(combo[t] * tip_alanlari[t] for t in tipler)
        daire_sayisi = sum(combo.values())

        if daire_sayisi == 0 or daire_sayisi > max_daire:
            continue

        # Tolerans içinde mi?
        if abs(toplam - toplam_alan) / toplam_alan <= tolerans:
            combos.append(combo)

    return combos
