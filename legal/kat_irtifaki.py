"""
Kat İrtifakı / Kat Mülkiyeti Belge Taslağı — Arsa payı hesabı ve bağımsız bölüm listesi.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BagimsizBolum:
    """Bağımsız bölüm kaydı."""
    bolum_no: int
    kat: int
    tip: str            # "daire", "dukkan", "depo"
    daire_tipi: str     # "3+1", "dükkan" vb.
    brut_alan: float
    net_alan: float
    arsa_payi_pay: int = 0
    arsa_payi_payda: int = 0
    eklentiler: list = field(default_factory=list)  # ["balkon", "depo"]


@dataclass
class KatIrtifakiTaslak:
    """Kat irtifakı belge taslağı."""
    proje_adi: str = ""
    il: str = ""
    ilce: str = ""
    ada: str = ""
    parsel: str = ""
    parsel_alani: float = 0.0
    toplam_insaat: float = 0.0
    bagimsiz_bolumler: list[BagimsizBolum] = field(default_factory=list)
    ortak_alanlar: list[str] = field(default_factory=list)
    tarih: str = ""
    uyari: str = "⚠️ Bu hukuki bir taslaktır. Kesinleştirmek için avukat onayı gereklidir."


def hesapla_arsa_payi(bagimsiz_bolumler: list[BagimsizBolum]) -> None:
    """Her bağımsız bölümün arsa payını hesaplar (m²'ye göre orantılı)."""
    toplam_alan = sum(b.brut_alan for b in bagimsiz_bolumler)
    if toplam_alan == 0:
        return

    # Payda: toplam brüt alanı 1000'e yuvarlayarak ortak payda bul
    payda = 1000
    for b in bagimsiz_bolumler:
        oran = b.brut_alan / toplam_alan
        b.arsa_payi_pay = max(1, round(oran * payda))
        b.arsa_payi_payda = payda


def olustur_kat_irtifaki(
    daireler: list[dict],
    proje_adi: str = "",
    il: str = "",
    ilce: str = "",
    ada: str = "",
    parsel: str = "",
    parsel_alani: float = 0.0,
    toplam_insaat: float = 0.0,
) -> KatIrtifakiTaslak:
    """Kat irtifakı belge taslağı oluşturur.

    Args:
        daireler: [{"daire_no": int, "kat": int, "tip": str, "brut_alan": float, "net_alan": float}, ...]
    """
    taslak = KatIrtifakiTaslak(
        proje_adi=proje_adi,
        il=il, ilce=ilce, ada=ada, parsel=parsel,
        parsel_alani=parsel_alani,
        toplam_insaat=toplam_insaat,
        tarih=datetime.now().strftime("%d.%m.%Y"),
    )

    for d in daireler:
        bb = BagimsizBolum(
            bolum_no=d.get("daire_no", 0),
            kat=d.get("kat", 1),
            tip="daire",
            daire_tipi=d.get("tip", "3+1"),
            brut_alan=d.get("brut_alan", 100),
            net_alan=d.get("net_alan", 80),
            eklentiler=d.get("eklentiler", ["balkon"]),
        )
        taslak.bagimsiz_bolumler.append(bb)

    # Arsa payı hesapla
    hesapla_arsa_payi(taslak.bagimsiz_bolumler)

    # Ortak alanlar
    taslak.ortak_alanlar = [
        "Ana giriş ve giriş holü",
        "Merdiven evi ve sahanlıklar",
        "Asansör ve asansör makine dairesi",
        "Çatı ve teras (ortak kullanım)",
        "Bahçe ve yeşil alanlar",
        "Otopark alanı",
        "Sığınak (varsa)",
        "Su deposu ve hidrofor odası",
        "Elektrik pano odası",
    ]

    return taslak


def taslak_to_text(taslak: KatIrtifakiTaslak) -> str:
    """Taslağı metin formatında döndürür."""
    lines = [
        "═" * 60,
        "KAT İRTİFAKI / KAT MÜLKİYETİ BELGE TASLAĞI",
        "═" * 60,
        "",
        f"Proje Adı    : {taslak.proje_adi}",
        f"İl / İlçe    : {taslak.il} / {taslak.ilce}",
        f"Ada / Parsel  : {taslak.ada} / {taslak.parsel}",
        f"Parsel Alanı  : {taslak.parsel_alani:.2f} m²",
        f"Toplam İnşaat : {taslak.toplam_insaat:.2f} m²",
        f"Tarih         : {taslak.tarih}",
        "",
        "─" * 60,
        "BAĞIMSIZ BÖLÜM LİSTESİ",
        "─" * 60,
        f"{'No':>4} {'Kat':>4} {'Tip':>6} {'Brüt m²':>10} {'Net m²':>10} {'Arsa Payı':>12}",
        "─" * 60,
    ]

    for bb in taslak.bagimsiz_bolumler:
        lines.append(
            f"{bb.bolum_no:>4} {bb.kat:>4} {bb.daire_tipi:>6} "
            f"{bb.brut_alan:>10.1f} {bb.net_alan:>10.1f} "
            f"{bb.arsa_payi_pay:>5}/{bb.arsa_payi_payda}"
        )

    lines.extend([
        "",
        "─" * 60,
        "ORTAK ALANLAR",
        "─" * 60,
    ])
    for i, oa in enumerate(taslak.ortak_alanlar, 1):
        lines.append(f"  {i}. {oa}")

    lines.extend([
        "",
        "─" * 60,
        taslak.uyari,
        "─" * 60,
    ])

    return "\n".join(lines)
