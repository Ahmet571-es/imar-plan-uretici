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
class KatIrtifakiSonucu:
    """Kat irtifakı hesaplama sonuçları."""
    toplam_bagimsiz_bolum: int = 0
    arsa_payi_paylari: list = field(default_factory=list)
    ortak_alan_listesi_detay: list = field(default_factory=list)
    yonetim_plani_maddeleri: list = field(default_factory=list)
    aidat_payi_orani: dict = field(default_factory=dict)
    tapu_harci_tahmini: float = 0.0


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
    sonuc: KatIrtifakiSonucu = field(default_factory=KatIrtifakiSonucu)
    uyari: str = "⚠️ Bu hukuki bir taslaktır. Kesinleştirmek için avukat onayı gereklidir."


# ── Standart yönetim planı maddeleri ──
STANDART_YONETIM_PLANI_MADDELERI = [
    "Yönetici, kat malikleri kurulunca en az bir yıl için seçilir.",
    "Kat malikleri kurulu yılda en az bir kez toplanır; olağanüstü toplantı "
    "kat maliklerinin 1/3'ünün talebi ile yapılır.",
    "Ortak giderler, bağımsız bölümlerin arsa payı oranında paylaştırılır.",
    "Aidatlar her ayın ilki ile beşi arasında yönetici hesabına yatırılır; "
    "gecikme halinde aylık %5 gecikme faizi uygulanır.",
    "Ortak alanlar (merdiven, asansör, bahçe, otopark) tüm kat maliklerinin "
    "eşit kullanımına açıktır; izinsiz tadilat yapılamaz.",
    "Bağımsız bölüm sahipleri, konut niteliğindeki bölümleri mesken dışı "
    "amaçla kullanamaz (kat malikleri kurulu kararı olmaksızın).",
    "Gürültü ve rahatsızlık veren faaliyetler 22:00-08:00 saatleri arasında yasaktır.",
    "Evcil hayvan beslenmesi, kat malikleri kurulunun belirlediği kurallara tabidir.",
    "Binanın dış cephesinde, kat malikleri kurulu izni olmadan değişiklik yapılamaz.",
    "Yönetici, her yıl gelir-gider hesabını kat malikleri kuruluna sunar "
    "ve ibra talep eder.",
    "Asansör, jeneratör ve ortak tesisat bakımları yönetici tarafından "
    "periyodik olarak yaptırılır.",
    "Yangın merdiveni, yangın tüpü ve sığınak gibi güvenlik ekipmanları "
    "yönetici sorumluluğundadır ve yıllık kontrolleri yapılır.",
    "İşbu yönetim planı, kat maliklerinin 4/5 çoğunluğu ile değiştirilebilir.",
]


# ── Ortak alan detayları ──
ORTAK_ALAN_DETAYLARI = [
    {
        "alan": "Merdiven evi ve sahanlıklar",
        "aciklama": "Tüm katlara erişim sağlayan ana merdiven boşluğu, sahanlıklar ve korkuluklar",
        "bakim": "Yıllık boya/badana, aydınlatma kontrolü",
    },
    {
        "alan": "Asansör ve asansör makine dairesi",
        "aciklama": "Yolcu asansörü, makine dairesi, kuyu dibi ve kabin",
        "bakim": "Aylık periyodik bakım, yıllık muayene (TSE)",
    },
    {
        "alan": "Sığınak",
        "aciklama": "Sivil savunma amaçlı sığınak alanı (İmar Yönetmeliği gereği zorunlu)",
        "bakim": "Havalandırma ve kapı kontrolü, yıllık denetim",
    },
    {
        "alan": "Bahçe ve yeşil alanlar",
        "aciklama": "Parsel sınırları dahilindeki bahçe, çim, ağaç ve peyzaj alanları",
        "bakim": "Mevsimsel bakım, sulama sistemi kontrolü",
    },
    {
        "alan": "Otopark alanı",
        "aciklama": "Açık veya kapalı otopark; araç kapasitesi imar planına göre belirlenir",
        "bakim": "Zemin kaplaması, aydınlatma ve çizgi bakımı",
    },
    {
        "alan": "Çatı ve teras",
        "aciklama": "Çatı örtüsü, su yalıtımı, çatı arası (varsa) ve ortak teras",
        "bakim": "Yıllık su yalıtım kontrolü, oluk temizliği",
    },
    {
        "alan": "Ana giriş ve giriş holü",
        "aciklama": "Binanın ana giriş kapısı, giriş holü, posta kutuları ve apartman panosu",
        "bakim": "Temizlik, aydınlatma, kapı kilidi ve interkom bakımı",
    },
    {
        "alan": "Su deposu ve hidrofor odası",
        "aciklama": "Bina su deposu, hidrofor pompası ve bağlantı tesisatı",
        "bakim": "6 aylık depo temizliği, pompa bakımı",
    },
    {
        "alan": "Elektrik pano odası",
        "aciklama": "Ana elektrik panosu, sayaçlar ve dağıtım kabloları",
        "bakim": "Yıllık termal kamera kontrolü, bağlantı sıkılığı",
    },
    {
        "alan": "Jeneratör odası (varsa)",
        "aciklama": "Ortak kullanıma ait jeneratör ve yakıt deposu",
        "bakim": "Aylık çalıştırma testi, yıllık genel bakım",
    },
]


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


def hesapla_tapu_harci(toplam_deger: float) -> float:
    """Tapu harcı tahmini hesaplar (toplam değer x %2).

    Tapu harcı, alıcı ve satıcı olmak üzere toplam %4 olup
    burada tek taraf payı (%2) hesaplanır.
    """
    return toplam_deger * 0.02


def hesapla_aidat_payi_orani(bagimsiz_bolumler: list[BagimsizBolum]) -> dict:
    """Her bağımsız bölüm için brüt alan bazlı aidat payı oranı hesaplar.

    Returns:
        {"bolum_no": {"brut_alan": float, "oran_yuzde": float, "pay": int, "payda": int}}
    """
    toplam_brut = sum(b.brut_alan for b in bagimsiz_bolumler)
    if toplam_brut == 0:
        return {}

    sonuc = {}
    for b in bagimsiz_bolumler:
        oran = b.brut_alan / toplam_brut
        sonuc[b.bolum_no] = {
            "brut_alan": b.brut_alan,
            "oran_yuzde": round(oran * 100, 2),
            "pay": b.arsa_payi_pay,
            "payda": b.arsa_payi_payda,
        }
    return sonuc


def olustur_kat_irtifaki(
    daireler: list[dict],
    proje_adi: str = "",
    il: str = "",
    ilce: str = "",
    ada: str = "",
    parsel: str = "",
    parsel_alani: float = 0.0,
    toplam_insaat: float = 0.0,
    toplam_deger: float = 0.0,
) -> KatIrtifakiTaslak:
    """Kat irtifakı belge taslağı oluşturur.

    Args:
        daireler: [{"daire_no": int, "kat": int, "tip": str, "brut_alan": float, "net_alan": float}, ...]
        toplam_deger: Gayrimenkulün toplam tahmini değeri (TL) — tapu harcı hesabı için.
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

    # Ortak alanlar (kısa liste — geriye dönük uyumluluk)
    taslak.ortak_alanlar = [detay["alan"] for detay in ORTAK_ALAN_DETAYLARI]

    # ── Sonuç hesaplamaları ──
    sonuc = KatIrtifakiSonucu()

    # Toplam bağımsız bölüm sayısı
    sonuc.toplam_bagimsiz_bolum = len(taslak.bagimsiz_bolumler)

    # Arsa payı pay detayları
    sonuc.arsa_payi_paylari = [
        {
            "bolum_no": bb.bolum_no,
            "kat": bb.kat,
            "daire_tipi": bb.daire_tipi,
            "brut_alan": bb.brut_alan,
            "arsa_payi_pay": bb.arsa_payi_pay,
            "arsa_payi_payda": bb.arsa_payi_payda,
        }
        for bb in taslak.bagimsiz_bolumler
    ]

    # Ortak alan detaylı listesi
    sonuc.ortak_alan_listesi_detay = list(ORTAK_ALAN_DETAYLARI)

    # Yönetim planı maddeleri
    sonuc.yonetim_plani_maddeleri = list(STANDART_YONETIM_PLANI_MADDELERI)

    # Aidat payı oranı (brüt alan bazlı)
    sonuc.aidat_payi_orani = hesapla_aidat_payi_orani(taslak.bagimsiz_bolumler)

    # Tapu harcı tahmini (toplam değer x %2)
    if toplam_deger > 0:
        sonuc.tapu_harci_tahmini = hesapla_tapu_harci(toplam_deger)
    else:
        # Değer verilmemişse m² birim fiyat tahmini ile hesapla
        tahmini_birim_fiyat = 30_000  # TL/m² (genel ortalama)
        tahmini_deger = toplam_insaat * tahmini_birim_fiyat
        sonuc.tapu_harci_tahmini = hesapla_tapu_harci(tahmini_deger)

    taslak.sonuc = sonuc
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
        f"Toplam Bağımsız Bölüm : {taslak.sonuc.toplam_bagimsiz_bolum}",
        "",
        "─" * 60,
        "ORTAK ALANLAR (DETAYLI)",
        "─" * 60,
    ])
    for i, detay in enumerate(taslak.sonuc.ortak_alan_listesi_detay, 1):
        lines.append(f"  {i}. {detay['alan']}")
        lines.append(f"     Açıklama : {detay['aciklama']}")
        lines.append(f"     Bakım    : {detay['bakim']}")
        lines.append("")

    lines.extend([
        "─" * 60,
        "AİDAT PAYI ORANLARI (BRÜT ALAN BAZLI)",
        "─" * 60,
        f"{'No':>4} {'Brüt m²':>10} {'Oran (%)':>10}",
        "─" * 40,
    ])
    for bolum_no, veri in taslak.sonuc.aidat_payi_orani.items():
        lines.append(
            f"{bolum_no:>4} {veri['brut_alan']:>10.1f} {veri['oran_yuzde']:>9.2f}%"
        )

    lines.extend([
        "",
        "─" * 60,
        "TAPU HARCI TAHMİNİ",
        "─" * 60,
        f"  Tahmini tapu harcı (tek taraf %2) : {taslak.sonuc.tapu_harci_tahmini:,.2f} TL",
        "",
        "─" * 60,
        "YÖNETİM PLANI MADDELERİ",
        "─" * 60,
    ])
    for i, madde in enumerate(taslak.sonuc.yonetim_plani_maddeleri, 1):
        lines.append(f"  Madde {i}: {madde}")

    lines.extend([
        "",
        "─" * 60,
        taslak.uyari,
        "─" * 60,
    ])

    return "\n".join(lines)
