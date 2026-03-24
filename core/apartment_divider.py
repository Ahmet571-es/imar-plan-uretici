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
