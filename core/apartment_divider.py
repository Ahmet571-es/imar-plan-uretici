"""
Daire Bölümleme Mantığı — Kat başına daire sayısı, tipi ve oda detayları.
"""

from dataclasses import dataclass, field
from config.room_defaults import DAIRE_SABLONLARI, get_default_rooms
from dataset.dataset_rules import APARTMENT_TYPE_STATS


@dataclass
class Oda:
    """Tek bir oda."""
    isim: str
    tip: str
    m2: float
    min_m2: float = 0.0
    max_m2: float = 0.0


@dataclass
class Daire:
    """Tek bir daire."""
    numara: int            # Daire numarası (bina genelinde)
    kat: int               # Hangi kat
    tip: str               # "1+1", "2+1", vb.
    brut_alan: float       # Brüt m²
    odalar: list[Oda] = field(default_factory=list)

    @property
    def net_alan(self) -> float:
        """Odaların toplam alanı (net)."""
        return sum(o.m2 for o in self.odalar)

    @property
    def duvar_kayip(self) -> float:
        """Duvar ve kayıp alanı."""
        return max(0, self.brut_alan - self.net_alan)

    def ozet_dict(self) -> dict:
        return {
            "Daire No": self.numara,
            "Kat": self.kat,
            "Tip": self.tip,
            "Brüt Alan (m²)": round(self.brut_alan, 1),
            "Net Alan (m²)": round(self.net_alan, 1),
            "Oda Sayısı": len(self.odalar),
        }


@dataclass
class KatPlani:
    """Bir kat."""
    kat_no: int
    brut_alan: float
    ortak_alan: float
    daireler: list[Daire] = field(default_factory=list)

    @property
    def net_kullanilabilir(self) -> float:
        return self.brut_alan - self.ortak_alan

    @property
    def kullanilan_alan(self) -> float:
        return sum(d.brut_alan for d in self.daireler)

    @property
    def kalan_alan(self) -> float:
        return self.net_kullanilabilir - self.kullanilan_alan


@dataclass
class BinaProgrami:
    """Tüm bina."""
    kat_sayisi: int
    katlar: list[KatPlani] = field(default_factory=list)

    @property
    def toplam_daire(self) -> int:
        return sum(len(k.daireler) for k in self.katlar)

    @property
    def toplam_insaat(self) -> float:
        return sum(k.brut_alan for k in self.katlar)

    def tum_daireler(self) -> list[Daire]:
        daireler = []
        for kat in self.katlar:
            daireler.extend(kat.daireler)
        return daireler


# ── Sıralı tip listesi (komşu tip aramada kullanılır) ─────────────
_TIP_SIRASI = ["1+1", "2+1", "3+1", "4+1", "5+1"]


def varsayilan_daireler_olustur(
    kat_basi_net_alan: float,
    kat_sayisi: int,
    kat_basi_brut_alan: float,
    ortak_alan: float,
    daire_sayisi_per_kat: int = 2,
    daire_tipi: str = "3+1",
) -> BinaProgrami:
    """Varsayılan parametrelerle bina programı oluşturur.

    Oda alanlarını şablona göre ölçekler, ardından iki aşamalı normalizasyon
    ve duvar-kayıp tahmini uygular:

      1) Post-scaling normalization — toplam oda alanını brüt alana göre
         kabul edilebilir banda (%70 - %85) çeker.
      2) Duvar-kayıp tahmini — oda sayısına bağlı wall_factor ile hesaplanır
         ve odalar hedef net alana oransal küçültülür.

    Args:
        kat_basi_net_alan: Dairelere kalan net alan (m²).
        kat_sayisi: Toplam kat sayısı.
        kat_basi_brut_alan: Kat başı brüt alan (m²).
        ortak_alan: Kat başı ortak alan (m²).
        daire_sayisi_per_kat: Her katta kaç daire.
        daire_tipi: Varsayılan daire tipi.

    Returns:
        BinaProgrami nesnesi.
    """
    bina = BinaProgrami(kat_sayisi=kat_sayisi)
    daire_no = 1

    for kat_no in range(1, kat_sayisi + 1):
        kat = KatPlani(
            kat_no=kat_no,
            brut_alan=kat_basi_brut_alan,
            ortak_alan=ortak_alan,
        )

        # Her daire için alan dağıtımı
        daire_brut = kat_basi_net_alan / max(daire_sayisi_per_kat, 1)

        for d_idx in range(daire_sayisi_per_kat):
            # Varsayılan odaları al
            varsayilan_odalar = get_default_rooms(daire_tipi)

            # Oda alanlarını daire brüt alanına göre orantılı ölçekle
            sablon = DAIRE_SABLONLARI.get(daire_tipi, {})
            sablon_brut = sablon.get("varsayilan_brut", daire_brut)
            olcek = daire_brut / sablon_brut if sablon_brut > 0 else 1.0

            odalar = []
            for vr in varsayilan_odalar:
                m2 = vr["varsayilan_m2"] * olcek
                # Min/max sınırlarına kırp
                m2 = max(vr["min_m2"], min(m2, vr["max_m2"]))
                odalar.append(Oda(
                    isim=vr["isim"],
                    tip=vr["tip"],
                    m2=round(m2, 1),
                    min_m2=vr["min_m2"],
                    max_m2=vr["max_m2"],
                ))

            # ── Adım 1: Post-scaling normalization ─────────────────
            # Kırpma sonrası toplam oda alanını hesapla ve brüt alana
            # göre kabul edilebilir aralığa çek.
            toplam_oda_alan = sum(o.m2 for o in odalar)
            ust_sinir = daire_brut * 0.85   # net alan brütün %85'ini geçmemeli
            alt_sinir = daire_brut * 0.70    # net alan brütün %70'inden az olmamalı

            if toplam_oda_alan > ust_sinir and toplam_oda_alan > 0:
                # Oransal küçültme — hiçbir odayı min_m2 altına düşürme
                kuculme_orani = ust_sinir / toplam_oda_alan
                for oda in odalar:
                    yeni = oda.m2 * kuculme_orani
                    oda.m2 = round(max(yeni, oda.min_m2), 1)

            elif toplam_oda_alan < alt_sinir and toplam_oda_alan > 0:
                # Oransal büyütme — her odayı max_m2'ye kadar, marjla orantılı
                eksik = alt_sinir - toplam_oda_alan
                marjlar = [oda.max_m2 - oda.m2 for oda in odalar]
                toplam_marj = sum(m for m in marjlar if m > 0)

                if toplam_marj > 0:
                    uygulanacak = min(eksik, toplam_marj)
                    for i, oda in enumerate(odalar):
                        if marjlar[i] > 0:
                            pay = (marjlar[i] / toplam_marj) * uygulanacak
                            oda.m2 = round(oda.m2 + pay, 1)

            # ── Adım 2: Duvar kayıp tahmini (oda sayısına bağlı) ──
            # Daha fazla oda → daha fazla iç duvar → daha yüksek kayıp
            wall_factor = 0.15 + (len(odalar) - 4) * 0.01
            wall_factor = max(0.15, min(wall_factor, 0.25))

            duvar_kayip_tahmini = daire_brut * wall_factor
            hedef_net = daire_brut - duvar_kayip_tahmini
            mevcut_net = sum(o.m2 for o in odalar)

            if mevcut_net > hedef_net and mevcut_net > 0:
                duvar_olcek = hedef_net / mevcut_net
                for oda in odalar:
                    yeni = oda.m2 * duvar_olcek
                    oda.m2 = round(max(yeni, oda.min_m2), 1)

            daire = Daire(
                numara=daire_no,
                kat=kat_no,
                tip=daire_tipi,
                brut_alan=round(daire_brut, 1),
                odalar=odalar,
            )
            kat.daireler.append(daire)
            daire_no += 1

        bina.katlar.append(kat)

    return bina


def daire_olustur_custom(
    kat_no: int,
    daire_no: int,
    daire_tipi: str,
    brut_alan: float,
    oda_listesi: list[dict] | None = None,
) -> Daire:
    """Özel parametrelerle tek bir daire oluşturur.

    Args:
        kat_no: Kat numarası.
        daire_no: Daire numarası.
        daire_tipi: Daire tipi ("1+1", "2+1", vb.).
        brut_alan: Dairenin brüt alanı (m²).
        oda_listesi: Oda listesi [{"isim": str, "tip": str, "m2": float}, ...].
                     None ise varsayılan şablondan oluşturulur.

    Returns:
        Daire nesnesi.
    """
    if oda_listesi is None:
        varsayilan = get_default_rooms(daire_tipi)
        sablon = DAIRE_SABLONLARI.get(daire_tipi, {})
        sablon_brut = sablon.get("varsayilan_brut", brut_alan)
        olcek = brut_alan / sablon_brut if sablon_brut > 0 else 1.0

        odalar = []
        for vr in varsayilan:
            m2 = vr["varsayilan_m2"] * olcek
            m2 = max(vr["min_m2"], min(m2, vr["max_m2"]))
            odalar.append(Oda(
                isim=vr["isim"],
                tip=vr["tip"],
                m2=round(m2, 1),
                min_m2=vr["min_m2"],
                max_m2=vr["max_m2"],
            ))
    else:
        odalar = []
        for od in oda_listesi:
            odalar.append(Oda(
                isim=od.get("isim", "Oda"),
                tip=od.get("tip", "diger"),
                m2=od.get("m2", 10.0),
                min_m2=od.get("min_m2", 0.0),
                max_m2=od.get("max_m2", 100.0),
            ))

    return Daire(
        numara=daire_no,
        kat=kat_no,
        tip=daire_tipi,
        brut_alan=brut_alan,
        odalar=odalar,
    )


# ══════════════════════════════════════════════════════════════════
# OPTİMİZASYON & ANALİZ FONKSİYONLARI
# ══════════════════════════════════════════════════════════════════

def optimize_daire_dagilimi(
    kat_basi_net_alan: float,
    kat_sayisi: int,
    kat_basi_brut_alan: float,
    ortak_alan: float,
    hedef_daire_tipi: str = "3+1",
    max_daire_per_kat: int = 4,
) -> BinaProgrami:
    """Optimum daire dağılımını hesaplar.

    Farklı daire sayısı/tip kombinasyonlarını dener,
    en iyi alan kullanımını ve tip uyumunu bulan konfigürasyonu seçer.

    Puanlama bileşenleri (toplam 100):
        area_fit_score   (0-40): Daire brüt alanının tip istatistik aralığına
                                  ve ortalamasına yakınlığı.
        type_match_score (0-30): Hedef tiple doğrudan eşleşme bonusu;
                                  komşu tiplere azalan bonus.
        efficiency_score (0-30): Kat alanının ne kadarının fiilen
                                  dairelere dağıtılabildiği.

    Args:
        kat_basi_net_alan: Dairelere kalan net alan (m²).
        kat_sayisi: Toplam kat sayısı.
        kat_basi_brut_alan: Kat başı brüt alan (m²).
        ortak_alan: Kat başı ortak alan (m²).
        hedef_daire_tipi: Tercih edilen daire tipi ("1+1" ... "5+1").
        max_daire_per_kat: Kat başına denenecek maksimum daire sayısı.

    Returns:
        BinaProgrami — en yüksek puanı alan konfigürasyon.
    """

    # ── Yardımcı puanlama fonksiyonları ────────────────────────────

    def _alan_uyum_puani(daire_brut: float, tip: str) -> float:
        """Brüt alanın tip istatistiklerine uyumunu 0-40 arası puanlar."""
        stats = APARTMENT_TYPE_STATS.get(tip)
        if stats is None:
            return 0.0
        min_g = stats["min_gross"]
        max_g = stats["max_gross"]
        avg_g = stats["avg_gross"]

        if min_g <= daire_brut <= max_g:
            # Aralık içinde — ortalamaya yakınlık oranında puan
            max_sapma = max(avg_g - min_g, max_g - avg_g, 1.0)
            sapma = abs(daire_brut - avg_g)
            return 40.0 * max(0.0, 1.0 - sapma / max_sapma)
        else:
            # Aralık dışı — dışarıda kalma miktarına göre düşen puan
            tasma = (min_g - daire_brut) if daire_brut < min_g else (daire_brut - max_g)
            return max(0.0, 20.0 - tasma * 1.0)

    def _tip_eslesme_puani(tip: str) -> float:
        """Hedef tiple eşleşirse 30, komşu tip 15, iki adım uzak 5."""
        if tip == hedef_daire_tipi:
            return 30.0
        hedef_idx = _TIP_SIRASI.index(hedef_daire_tipi) if hedef_daire_tipi in _TIP_SIRASI else -1
        tip_idx = _TIP_SIRASI.index(tip) if tip in _TIP_SIRASI else -1
        if hedef_idx >= 0 and tip_idx >= 0:
            uzaklik = abs(hedef_idx - tip_idx)
            if uzaklik == 1:
                return 15.0
            if uzaklik == 2:
                return 5.0
        return 0.0

    def _en_uygun_tip(daire_brut: float) -> str:
        """Verilen brüt alan için en uygun daire tipini belirler.

        Hedef tip uyuyorsa doğrudan döner; yoksa mesafeye göre
        sıralı komşu tipleri dener, toplam puana göre seçer.
        """
        stats = APARTMENT_TYPE_STATS.get(hedef_daire_tipi)
        if stats and stats["min_gross"] <= daire_brut <= stats["max_gross"]:
            return hedef_daire_tipi

        hedef_idx = (
            _TIP_SIRASI.index(hedef_daire_tipi)
            if hedef_daire_tipi in _TIP_SIRASI
            else len(_TIP_SIRASI) // 2
        )
        adaylar = sorted(
            _TIP_SIRASI,
            key=lambda t: abs(_TIP_SIRASI.index(t) - hedef_idx),
        )

        en_iyi_tip = hedef_daire_tipi
        en_iyi_p = -1.0
        for tip in adaylar:
            p = _alan_uyum_puani(daire_brut, tip) + _tip_eslesme_puani(tip)
            if p > en_iyi_p:
                en_iyi_p = p
                en_iyi_tip = tip
        return en_iyi_tip

    # ── Tüm kombinasyonları puanla ─────────────────────────────────
    en_iyi_puan = -1.0
    en_iyi_kombi: tuple[int, str] | None = None

    for daire_sayisi in range(1, max_daire_per_kat + 1):
        daire_brut = kat_basi_net_alan / daire_sayisi
        tip = _en_uygun_tip(daire_brut)

        area_fit = _alan_uyum_puani(daire_brut, tip)
        type_match = _tip_eslesme_puani(tip)

        # Verimlilik: kullanılan alan / mevcut net alan
        kullanilan = daire_brut * daire_sayisi
        verimlilik = kullanilan / kat_basi_net_alan if kat_basi_net_alan > 0 else 0.0
        efficiency = 30.0 * min(verimlilik, 1.0)

        toplam = area_fit + type_match + efficiency

        if toplam > en_iyi_puan:
            en_iyi_puan = toplam
            en_iyi_kombi = (daire_sayisi, tip)

    # Fallback
    if en_iyi_kombi is None:
        en_iyi_kombi = (2, hedef_daire_tipi)

    secilen_daire_sayisi, secilen_tip = en_iyi_kombi

    # ── Seçilen konfigürasyonla bina programı oluştur ──────────────
    return varsayilan_daireler_olustur(
        kat_basi_net_alan=kat_basi_net_alan,
        kat_sayisi=kat_sayisi,
        kat_basi_brut_alan=kat_basi_brut_alan,
        ortak_alan=ortak_alan,
        daire_sayisi_per_kat=secilen_daire_sayisi,
        daire_tipi=secilen_tip,
    )


def analiz_bina_programi(bina: BinaProgrami) -> dict:
    """Bina programı detaylı analizi.

    Toplam daire sayısı, tip dağılımı, alan istatistikleri, verimlilik ve
    tip uyum puanı hesaplar.  Sonuçlara dayalı iyileştirme önerileri üretir.

    Returns:
        {
            "toplam_daire": int,
            "tip_dagilimi": {"3+1": 4, "2+1": 2, ...},
            "ortalama_daire_alan": float,
            "en_kucuk_daire": float,
            "en_buyuk_daire": float,
            "alan_verimlilik": float,  # kullanilan/mevcut
            "duvar_kayip_ortalama": float,
            "tip_uyum_puani": float,  # 0-100
            "oneriler": list[str],
        }
    """
    tum = bina.tum_daireler()

    if not tum:
        return {
            "toplam_daire": 0,
            "tip_dagilimi": {},
            "ortalama_daire_alan": 0.0,
            "en_kucuk_daire": 0.0,
            "en_buyuk_daire": 0.0,
            "alan_verimlilik": 0.0,
            "duvar_kayip_ortalama": 0.0,
            "tip_uyum_puani": 0.0,
            "oneriler": ["Binada daire bulunamadı."],
        }

    # ── Temel istatistikler ────────────────────────────────────────
    toplam_daire = len(tum)

    tip_dagilimi: dict[str, int] = {}
    for d in tum:
        tip_dagilimi[d.tip] = tip_dagilimi.get(d.tip, 0) + 1

    brut_alanlar = [d.brut_alan for d in tum]
    ortalama_daire_alan = sum(brut_alanlar) / toplam_daire
    en_kucuk_daire = min(brut_alanlar)
    en_buyuk_daire = max(brut_alanlar)

    # ── Alan verimliliği ───────────────────────────────────────────
    toplam_kullanilan = sum(d.brut_alan for d in tum)
    toplam_mevcut = sum(k.net_kullanilabilir for k in bina.katlar)
    alan_verimlilik = (
        toplam_kullanilan / toplam_mevcut if toplam_mevcut > 0 else 0.0
    )

    # ── Duvar kayıp ortalaması ─────────────────────────────────────
    kayiplar = [d.duvar_kayip for d in tum]
    duvar_kayip_ortalama = sum(kayiplar) / toplam_daire

    # ── Tip uyum puanı (0-100) ─────────────────────────────────────
    # Her dairenin brüt alanının kendi tip istatistiğine uyumunu ölçer.
    tip_puanlari: list[float] = []
    for d in tum:
        stats = APARTMENT_TYPE_STATS.get(d.tip)
        if stats is None:
            tip_puanlari.append(50.0)
            continue

        min_g = stats["min_gross"]
        max_g = stats["max_gross"]
        avg_g = stats["avg_gross"]

        if min_g <= d.brut_alan <= max_g:
            max_sapma = max(avg_g - min_g, max_g - avg_g, 1.0)
            sapma = abs(d.brut_alan - avg_g)
            tip_puanlari.append(100.0 * max(0.0, 1.0 - 0.5 * sapma / max_sapma))
        else:
            tasma = (min_g - d.brut_alan) if d.brut_alan < min_g else (d.brut_alan - max_g)
            tip_puanlari.append(max(0.0, 50.0 - tasma * 1.5))

    tip_uyum_puani = sum(tip_puanlari) / len(tip_puanlari) if tip_puanlari else 0.0

    # ── Öneriler ───────────────────────────────────────────────────
    oneriler: list[str] = []

    if alan_verimlilik < 0.85:
        oneriler.append(
            f"Alan verimliliği düşük ({alan_verimlilik:.0%}). "
            f"Kat başına daire sayısını artırmayı veya daire tipini büyütmeyi düşünün."
        )
    elif alan_verimlilik > 0.98:
        oneriler.append(
            "Alan kullanımı çok sıkışık (>%98). Ortak alan ve sirkülasyon "
            "alanlarının yeterliliğini kontrol edin."
        )

    if ortalama_daire_alan > 0 and duvar_kayip_ortalama / ortalama_daire_alan > 0.25:
        oneriler.append(
            f"Duvar kayıp oranı yüksek ({duvar_kayip_ortalama:.1f} m\u00b2 / daire). "
            f"Oda sayısını azaltmayı veya açık mutfak planı uygulamayı düşünün."
        )

    if tip_uyum_puani < 60:
        oneriler.append(
            f"Tip uyum puanı düşük ({tip_uyum_puani:.0f}/100). Daire alanları "
            f"seçilen tiplerin ideal aralığına uymuyor. Farklı tip veya daire "
            f"sayısı deneyin."
        )

    if en_buyuk_daire > 0 and (en_buyuk_daire - en_kucuk_daire) / en_buyuk_daire > 0.40:
        oneriler.append(
            f"Daireler arasında büyük alan farkı var "
            f"({en_kucuk_daire:.0f} - {en_buyuk_daire:.0f} m\u00b2). "
            f"Daha homojen dağılım satış/kiralama açısından avantajlı olabilir."
        )

    for d in tum:
        if d.brut_alan > 0 and d.net_alan / d.brut_alan < 0.70:
            oneriler.append(
                f"Daire {d.numara} net/brüt oranı çok düşük "
                f"({d.net_alan / d.brut_alan:.0%}). Oda düzenini gözden geçirin."
            )
            break

    if not oneriler:
        oneriler.append("Bina programı genel olarak dengeli görünüyor.")

    return {
        "toplam_daire": toplam_daire,
        "tip_dagilimi": tip_dagilimi,
        "ortalama_daire_alan": round(ortalama_daire_alan, 1),
        "en_kucuk_daire": round(en_kucuk_daire, 1),
        "en_buyuk_daire": round(en_buyuk_daire, 1),
        "alan_verimlilik": round(alan_verimlilik, 4),
        "duvar_kayip_ortalama": round(duvar_kayip_ortalama, 1),
        "tip_uyum_puani": round(tip_uyum_puani, 1),
        "oneriler": oneriler,
    }
