"""
Daire Bölümleme Mantığı — Kat başına daire sayısı, tipi ve oda detayları.
"""

from dataclasses import dataclass, field
from config.room_defaults import DAIRE_SABLONLARI, get_default_rooms


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


def varsayilan_daireler_olustur(
    kat_basi_net_alan: float,
    kat_sayisi: int,
    kat_basi_brut_alan: float,
    ortak_alan: float,
    daire_sayisi_per_kat: int = 2,
    daire_tipi: str = "3+1",
) -> BinaProgrami:
    """Varsayılan parametrelerle bina programı oluşturur.

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


# ══════════════════════════════════════════════════════════════
# DERİNLEŞTİRİLMİŞ DAİRE OPTİMİZASYONU
# ══════════════════════════════════════════════════════════════

def optimize_daire_dagilimi(
    kat_basi_net_alan: float,
    kat_sayisi: int,
    kat_basi_brut_alan: float,
    ortak_alan: float,
    hedef_daire_tipi: str = "3+1",
    max_daire_per_kat: int = 4,
) -> BinaProgrami:
    """Optimum daire dağılımını hesaplar — farklı kombinasyonları dener.

    Farklı daire sayısı/tip kombinasyonlarını dener,
    en iyi alan kullanımını ve tip uyumunu bulan konfigürasyonu seçer.

    Returns:
        En yüksek puanlı BinaProgrami.
    """
    try:
        from dataset.dataset_rules import APARTMENT_TYPE_STATS
    except ImportError:
        APARTMENT_TYPE_STATS = {}

    tipler = ["1+1", "2+1", "3+1", "4+1", "5+1"]
    en_iyi_puan = -1
    en_iyi_bina = None
    en_iyi_bilgi = {}

    for daire_sayisi in range(1, max_daire_per_kat + 1):
        daire_brut = kat_basi_net_alan / daire_sayisi

        # Bu alan için en uygun daire tipini bul
        en_uygun_tip = hedef_daire_tipi
        en_iyi_tip_puan = 0

        for tip in tipler:
            stats = APARTMENT_TYPE_STATS.get(tip, {})
            min_g = stats.get("min_gross", 40)
            max_g = stats.get("max_gross", 300)
            avg_g = stats.get("avg_gross", 100)

            if min_g <= daire_brut <= max_g:
                # Alan ortalamaya ne kadar yakın?
                uzaklik = abs(daire_brut - avg_g) / max(avg_g, 1)
                alan_puani = max(0, 100 - uzaklik * 100)

                # Hedef tipe yakınlık bonusu
                tip_bonusu = 20 if tip == hedef_daire_tipi else 0

                toplam = alan_puani + tip_bonusu
                if toplam > en_iyi_tip_puan:
                    en_iyi_tip_puan = toplam
                    en_uygun_tip = tip

        # Verimlilik puanı: kullanılan / mevcut alan
        kullanilan = daire_brut * daire_sayisi
        verimlilik = kullanilan / max(kat_basi_net_alan, 1)
        verimlilik_puani = max(0, 100 - abs(1 - verimlilik) * 200)

        # Genel puan
        puan = en_iyi_tip_puan * 0.6 + verimlilik_puani * 0.4

        if puan > en_iyi_puan:
            en_iyi_puan = puan
            en_iyi_bilgi = {
                "daire_sayisi": daire_sayisi,
                "daire_tipi": en_uygun_tip,
                "daire_brut": daire_brut,
                "puan": puan,
            }

    # En iyi konfigürasyon ile bina programı oluştur
    if en_iyi_bilgi:
        en_iyi_bina = varsayilan_daireler_olustur(
            kat_basi_net_alan=kat_basi_net_alan,
            kat_sayisi=kat_sayisi,
            kat_basi_brut_alan=kat_basi_brut_alan,
            ortak_alan=ortak_alan,
            daire_sayisi_per_kat=en_iyi_bilgi["daire_sayisi"],
            daire_tipi=en_iyi_bilgi["daire_tipi"],
        )
    else:
        en_iyi_bina = varsayilan_daireler_olustur(
            kat_basi_net_alan, kat_sayisi, kat_basi_brut_alan, ortak_alan,
        )

    return en_iyi_bina


def analiz_bina_programi(bina: BinaProgrami) -> dict:
    """Bina programı detaylı analizi.

    Returns:
        dict: Tip dağılımı, alan verimlilik, duvar kayıp, tip uyum puanı ve öneriler.
    """
    tum_daireler = bina.tum_daireler()
    if not tum_daireler:
        return {"toplam_daire": 0, "oneriler": ["Henüz daire oluşturulmamış"]}

    tip_sayac = {}
    daire_alanlar = []
    duvar_kayiplar = []

    for d in tum_daireler:
        tip_sayac[d.tip] = tip_sayac.get(d.tip, 0) + 1
        daire_alanlar.append(d.brut_alan)
        if d.brut_alan > 0:
            duvar_kayiplar.append(d.duvar_kayip / d.brut_alan)

    # Toplam kullanılan alan
    toplam_kullanilan = sum(k.kullanilan_alan for k in bina.katlar)
    toplam_mevcut = sum(k.net_kullanilabilir for k in bina.katlar)
    verimlilik = toplam_kullanilan / max(toplam_mevcut, 1)

    # Tip uyum puanı (homojen dağılım daha iyi)
    tip_cesitlilik = len(tip_sayac)
    if tip_cesitlilik == 1:
        tip_uyum = 90  # Homojen — iyi
    elif tip_cesitlilik == 2:
        tip_uyum = 80  # 2 tip — kabul edilebilir
    else:
        tip_uyum = 60  # 3+ tip — karmaşık

    # Öneriler
    oneriler = []
    if verimlilik < 0.85:
        oneriler.append(f"Alan verimliliği düşük (%{verimlilik*100:.0f}). Daire sayısını artırabilirsiniz.")
    if verimlilik > 0.98:
        oneriler.append("Daireler çok sıkışık. Ortak alanlara yeterli yer bırakıldığından emin olun.")

    avg_kayip = sum(duvar_kayiplar) / max(len(duvar_kayiplar), 1)
    if avg_kayip < 0.12:
        oneriler.append(f"Duvar kayıp oranı düşük (%{avg_kayip*100:.0f}). Oda alanları gerçekçi mi kontrol edin.")
    elif avg_kayip > 0.28:
        oneriler.append(f"Duvar kayıp oranı yüksek (%{avg_kayip*100:.0f}). Alan israfı olabilir.")

    if not oneriler:
        oneriler.append("Bina programı dengeli ve verimli görünüyor.")

    return {
        "toplam_daire": len(tum_daireler),
        "tip_dagilimi": tip_sayac,
        "ortalama_daire_alan": round(sum(daire_alanlar) / max(len(daire_alanlar), 1), 1),
        "en_kucuk_daire": round(min(daire_alanlar), 1),
        "en_buyuk_daire": round(max(daire_alanlar), 1),
        "alan_verimlilik": round(verimlilik, 2),
        "duvar_kayip_ortalama": round(avg_kayip, 2),
        "tip_uyum_puani": tip_uyum,
        "oneriler": oneriler,
    }
