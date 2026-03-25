"""
İnşaat Süresi Tahmini — Gantt chart ile proje takvimi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import plotly.figure_factory as ff
import plotly.graph_objects as go
import math


@dataclass
class IsKalemi:
    """Bir iş kalemi."""
    isim: str
    sure_hafta_min: int
    sure_hafta_max: int
    baslangic_offset_hafta: int = 0  # Projenin başlangıcından itibaren
    paralel_grup: str = ""           # Paralel çalışabilecek iş grubu
    kritik_yol: bool = False
    faz: str = ""                    # Hangi faza ait
    bagimliliklar: list = field(default_factory=list)  # Bağımlı olduğu iş isimleri


# ── İş kalemleri şablonu (konut bina) ──
def get_is_kalemleri(kat_sayisi: int = 4, bodrum_var: bool = False) -> list[IsKalemi]:
    """Kat sayısına göre detaylı iş kalemlerini oluşturur."""
    kalemler = []
    offset = 0

    # ── 1. FAZ: Hazırlık & Temel ──
    kalemler.append(IsKalemi(
        "Şantiye Kurulumu", 1, 2, offset, "hazirlik", True,
        faz="Hazırlık", bagimliliklar=[],
    ))
    offset += 1

    kalemler.append(IsKalemi(
        "Hafriyat", 2, 3, offset, "temel", True,
        faz="Temel", bagimliliklar=["Şantiye Kurulumu"],
    ))
    hafriyat_bitis = offset + 3

    kalemler.append(IsKalemi(
        "Temel (Radye / Perde)", 3, 4, hafriyat_bitis, "temel", True,
        faz="Temel", bagimliliklar=["Hafriyat"],
    ))
    temel_bitis = hafriyat_bitis + 4
    offset = temel_bitis

    if bodrum_var:
        kalemler.append(IsKalemi(
            "Bodrum Kat Betonarme", 3, 4, offset, "temel", True,
            faz="Temel", bagimliliklar=["Temel (Radye / Perde)"],
        ))
        kalemler.append(IsKalemi(
            "Bodrum Su Yalıtımı", 1, 2, offset + 3, "temel", False,
            faz="Temel", bagimliliklar=["Bodrum Kat Betonarme"],
        ))
        offset += 5

    # ── 2. FAZ: Kaba İnşaat (kat bazlı) ──
    kaba_per_kat = 2.5  # hafta/kat
    kaba_offset = offset

    # Kat bazlı kaba inşaat
    for kat_no in range(1, kat_sayisi + 1):
        kat_sure_min = max(2, int(kaba_per_kat))
        kat_sure_max = max(3, int(kaba_per_kat) + 1)

        if kat_no == 1:
            bagimli = ["Bodrum Kat Betonarme"] if bodrum_var else ["Temel (Radye / Perde)"]
        else:
            bagimli = [f"Kaba İnşaat — {kat_no - 1}. Kat"]

        kalemler.append(IsKalemi(
            f"Kaba İnşaat — {kat_no}. Kat", kat_sure_min, kat_sure_max,
            kaba_offset, "kaba", True,
            faz="Kaba İnşaat", bagimliliklar=bagimli,
        ))
        kaba_offset += kat_sure_min

    kaba_bitis = kaba_offset
    toplam_kaba_sure = kaba_bitis - offset

    # Çatı
    kalemler.append(IsKalemi(
        "Çatı İnşaatı", 2, 3, kaba_bitis, "kaba", True,
        faz="Kaba İnşaat", bagimliliklar=[f"Kaba İnşaat — {kat_sayisi}. Kat"],
    ))
    cati_bitis = kaba_bitis + 3

    # ── 3. FAZ: Dış Cephe ──
    # Son 2 kat bitince dış cephe başlayabilir
    dis_cephe_baslangic = max(kaba_bitis - 4, offset + 2)
    kalemler.append(IsKalemi(
        "Dış Cephe Mantolama", 3, 5, dis_cephe_baslangic, "dis_cephe", False,
        faz="Dış Cephe", bagimliliklar=[f"Kaba İnşaat — {max(1, kat_sayisi - 1)}. Kat"],
    ))
    kalemler.append(IsKalemi(
        "Dış Cephe Boyası & Kaplama", 2, 3, dis_cephe_baslangic + 4, "dis_cephe", False,
        faz="Dış Cephe", bagimliliklar=["Dış Cephe Mantolama"],
    ))

    # ── 4. FAZ: Tesisat (kaba inşaatın %40'ı bitince başlar) ──
    tesisat_baslangic = offset + int(toplam_kaba_sure * 0.4)
    kalemler.append(IsKalemi(
        "Elektrik Tesisatı (Kaba)", 3, 5, tesisat_baslangic, "tesisat", False,
        faz="Tesisat", bagimliliklar=[f"Kaba İnşaat — {max(1, kat_sayisi // 2)}. Kat"],
    ))
    kalemler.append(IsKalemi(
        "Su & Kanalizasyon Tesisatı", 3, 5, tesisat_baslangic, "tesisat", False,
        faz="Tesisat", bagimliliklar=[f"Kaba İnşaat — {max(1, kat_sayisi // 2)}. Kat"],
    ))
    kalemler.append(IsKalemi(
        "Doğalgaz Tesisatı", 2, 3, tesisat_baslangic + 3, "tesisat", False,
        faz="Tesisat", bagimliliklar=["Su & Kanalizasyon Tesisatı"],
    ))
    kalemler.append(IsKalemi(
        "Yangın Tesisatı", 2, 3, tesisat_baslangic + 4, "tesisat", False,
        faz="Tesisat", bagimliliklar=["Elektrik Tesisatı (Kaba)"],
    ))

    # ── 5. FAZ: İnce İşler ──
    ince_baslangic = cati_bitis
    kalemler.append(IsKalemi(
        "İç Sıva", 3, 5, ince_baslangic, "ince", True,
        faz="İnce İşler", bagimliliklar=["Çatı İnşaatı"],
    ))
    kalemler.append(IsKalemi(
        "Şap & Tesviye", 2, 3, ince_baslangic + 3, "ince", True,
        faz="İnce İşler", bagimliliklar=["İç Sıva"],
    ))
    kalemler.append(IsKalemi(
        "Döşeme & Kaplama (Seramik/Parke)", 3, 4, ince_baslangic + 6, "ince", True,
        faz="İnce İşler", bagimliliklar=["Şap & Tesviye"],
    ))
    kalemler.append(IsKalemi(
        "Boya & Badana", 3, 4, ince_baslangic + 9, "ince", True,
        faz="İnce İşler", bagimliliklar=["Döşeme & Kaplama (Seramik/Parke)"],
    ))
    kalemler.append(IsKalemi(
        "Mutfak & Banyo Dolapları", 2, 3, ince_baslangic + 8, "ince", False,
        faz="İnce İşler", bagimliliklar=["Döşeme & Kaplama (Seramik/Parke)"],
    ))
    kalemler.append(IsKalemi(
        "Kapı Montajı (İç Kapılar)", 2, 3, ince_baslangic + 10, "montaj", False,
        faz="İnce İşler", bagimliliklar=["Boya & Badana"],
    ))
    kalemler.append(IsKalemi(
        "Pencere Montajı (PVC/Alüminyum)", 2, 3, ince_baslangic + 4, "montaj", False,
        faz="İnce İşler", bagimliliklar=["İç Sıva"],
    ))

    # ── 6. FAZ: Tesisat (İnce) ──
    ince_tesisat_baslangic = ince_baslangic + 5
    kalemler.append(IsKalemi(
        "Elektrik Tesisatı (İnce) & Armatür", 2, 3, ince_tesisat_baslangic + 6, "tesisat_ince", False,
        faz="Tesisat (İnce)", bagimliliklar=["Boya & Badana"],
    ))
    kalemler.append(IsKalemi(
        "Sıhhi Tesisat Armatürleri", 2, 3, ince_tesisat_baslangic + 6, "tesisat_ince", False,
        faz="Tesisat (İnce)", bagimliliklar=["Mutfak & Banyo Dolapları"],
    ))
    kalemler.append(IsKalemi(
        "Kombi / Kazan Montajı", 1, 2, ince_tesisat_baslangic + 8, "tesisat_ince", False,
        faz="Tesisat (İnce)", bagimliliklar=["Doğalgaz Tesisatı"],
    ))

    # ── 7. FAZ: Montaj & Mekanik ──
    asansor_baslangic = cati_bitis + 2
    kalemler.append(IsKalemi(
        "Asansör Montajı", 4, 6, asansor_baslangic, "montaj", False,
        faz="Montaj", bagimliliklar=["Çatı İnşaatı"],
    ))

    # ── 8. FAZ: Çevre & Son İşler ──
    son_isler_baslangic = ince_baslangic + 12
    kalemler.append(IsKalemi(
        "Peyzaj & Çevre Düzeni", 2, 3, son_isler_baslangic, "cevre", False,
        faz="Çevre & Son İşler", bagimliliklar=["Dış Cephe Boyası & Kaplama"],
    ))
    kalemler.append(IsKalemi(
        "Genel Temizlik", 1, 2, son_isler_baslangic + 3, "final", True,
        faz="Çevre & Son İşler", bagimliliklar=["Boya & Badana", "Peyzaj & Çevre Düzeni"],
    ))
    kalemler.append(IsKalemi(
        "Teknik Kontrol & Test", 1, 2, son_isler_baslangic + 4, "final", True,
        faz="Çevre & Son İşler", bagimliliklar=["Genel Temizlik"],
    ))
    kalemler.append(IsKalemi(
        "İskan Başvurusu & Onay", 2, 4, son_isler_baslangic + 6, "final", True,
        faz="Çevre & Son İşler", bagimliliklar=["Teknik Kontrol & Test"],
    ))

    return kalemler


@dataclass
class TimelineSonucu:
    """İnşaat süresi sonucu."""
    is_kalemleri: list[dict] = field(default_factory=list)
    toplam_sure_hafta_min: int = 0
    toplam_sure_hafta_max: int = 0
    toplam_sure_ay: float = 0.0
    tahmini_bitis: str = ""
    kritik_yol_suresi: int = 0

    # ── Yeni detay alanları ──
    kritik_yol: list = field(default_factory=list)        # critical path task names
    faz_ozeti: dict = field(default_factory=dict)         # phase summaries
    toplam_sure_ay_min: float = 0.0
    toplam_sure_ay_max: float = 0.0
    baslangic_tarihi: str = ""
    bitis_tarihi_min: str = ""
    bitis_tarihi_max: str = ""


def _hesapla_kritik_yol(kalemler: list[IsKalemi]) -> tuple[list[str], int]:
    """
    Kritik yolu hesaplar: her iş kaleminin en erken bitiş zamanını
    bağımlılıklar üzerinden hesaplar, en uzun yolu bulur.
    Dönüş: (kritik yol iş isimleri listesi, toplam süre hafta).
    """
    # İsimden iş kalemine map
    kalem_map = {k.isim: k for k in kalemler}

    # Her iş kalemi için en erken bitiş (EF) ve en erken başlangıç (ES)
    ef = {}  # isim -> earliest finish (hafta)
    es = {}  # isim -> earliest start (hafta)
    pred = {}  # isim -> hangi bağımlılıktan geldi (backtrack için)

    def get_ef(isim: str) -> int:
        if isim in ef:
            return ef[isim]
        k = kalem_map.get(isim)
        if k is None:
            return 0
        orta_sure = (k.sure_hafta_min + k.sure_hafta_max) // 2

        if not k.bagimliliklar:
            # Bağımlılığı yok, offset'ten başla
            es[isim] = k.baslangic_offset_hafta
            ef[isim] = k.baslangic_offset_hafta + orta_sure
            pred[isim] = None
        else:
            # En geç biten bağımlılıktan sonra başla
            max_dep_ef = 0
            max_dep_name = None
            for dep in k.bagimliliklar:
                dep_ef = get_ef(dep) if dep in kalem_map else 0
                if dep_ef > max_dep_ef:
                    max_dep_ef = dep_ef
                    max_dep_name = dep

            actual_start = max(k.baslangic_offset_hafta, max_dep_ef)
            es[isim] = actual_start
            ef[isim] = actual_start + orta_sure
            pred[isim] = max_dep_name

        return ef[isim]

    # Tüm kalemlerin EF'sini hesapla
    for k in kalemler:
        get_ef(k.isim)

    # Kritik yol: en geç biten iş kaleminden geriye backtrack
    if not ef:
        return [], 0

    son_kalem = max(ef, key=ef.get)
    kritik_suresi = ef[son_kalem]

    yol = []
    current = son_kalem
    while current is not None:
        yol.append(current)
        current = pred.get(current)
    yol.reverse()

    return yol, kritik_suresi


def hesapla_sure(
    kat_sayisi: int = 4,
    bodrum_var: bool = False,
    baslangic_tarihi: datetime | None = None,
) -> TimelineSonucu:
    """İnşaat süresini hesaplar."""
    if baslangic_tarihi is None:
        baslangic_tarihi = datetime.now()

    kalemler = get_is_kalemleri(kat_sayisi, bodrum_var)
    sonuc = TimelineSonucu()
    sonuc.baslangic_tarihi = baslangic_tarihi.strftime("%d.%m.%Y")

    # ── Kritik yol hesapla ──
    kritik_yol_isimleri, kritik_suresi = _hesapla_kritik_yol(kalemler)
    sonuc.kritik_yol = kritik_yol_isimleri
    sonuc.kritik_yol_suresi = kritik_suresi
    kritik_set = set(kritik_yol_isimleri)

    # ── İş kalemlerini hesapla ──
    kalem_map = {k.isim: k for k in kalemler}

    # Gerçek başlangıç/bitiş hesabı (bağımlılık tabanlı)
    ef_cache = {}
    es_cache = {}

    def get_actual_start(k: IsKalemi) -> int:
        if k.isim in es_cache:
            return es_cache[k.isim]
        if not k.bagimliliklar:
            es_cache[k.isim] = k.baslangic_offset_hafta
        else:
            max_dep = 0
            for dep in k.bagimliliklar:
                dep_k = kalem_map.get(dep)
                if dep_k:
                    dep_start = get_actual_start(dep_k)
                    dep_sure = (dep_k.sure_hafta_min + dep_k.sure_hafta_max) // 2
                    dep_end = dep_start + dep_sure
                    max_dep = max(max_dep, dep_end)
            es_cache[k.isim] = max(k.baslangic_offset_hafta, max_dep)
        return es_cache[k.isim]

    max_bitis_min = 0
    max_bitis_max = 0
    max_bitis_orta = 0

    # Faz bazlı toplama
    faz_data = {}  # faz -> {"min_baslangic", "max_bitis", "kalem_sayisi", "kalemler"}

    for k in kalemler:
        actual_start_hafta = get_actual_start(k)
        orta_sure = (k.sure_hafta_min + k.sure_hafta_max) // 2
        bitis_hafta_orta = actual_start_hafta + orta_sure
        bitis_hafta_min = actual_start_hafta + k.sure_hafta_min
        bitis_hafta_max = actual_start_hafta + k.sure_hafta_max

        max_bitis_min = max(max_bitis_min, bitis_hafta_min)
        max_bitis_max = max(max_bitis_max, bitis_hafta_max)
        max_bitis_orta = max(max_bitis_orta, bitis_hafta_orta)

        baslangic = baslangic_tarihi + timedelta(weeks=actual_start_hafta)
        bitis_tarih = baslangic + timedelta(weeks=orta_sure)
        bitis_tarih_min = baslangic + timedelta(weeks=k.sure_hafta_min)
        bitis_tarih_max = baslangic + timedelta(weeks=k.sure_hafta_max)

        is_kritik = k.isim in kritik_set

        sonuc.is_kalemleri.append({
            "isim": k.isim,
            "sure_hafta": orta_sure,
            "sure_hafta_min": k.sure_hafta_min,
            "sure_hafta_max": k.sure_hafta_max,
            "baslangic": baslangic.strftime("%Y-%m-%d"),
            "bitis": bitis_tarih.strftime("%Y-%m-%d"),
            "bitis_min": bitis_tarih_min.strftime("%Y-%m-%d"),
            "bitis_max": bitis_tarih_max.strftime("%Y-%m-%d"),
            "kritik_yol": is_kritik,
            "faz": k.faz,
            "paralel_grup": k.paralel_grup,
            "bagimliliklar": k.bagimliliklar,
            "baslangic_hafta": actual_start_hafta,
            "bitis_hafta": bitis_hafta_orta,
        })

        # Faz özeti topla
        if k.faz:
            if k.faz not in faz_data:
                faz_data[k.faz] = {
                    "min_baslangic_hafta": actual_start_hafta,
                    "max_bitis_hafta": bitis_hafta_orta,
                    "max_bitis_hafta_max": bitis_hafta_max,
                    "kalem_sayisi": 0,
                    "kalemler": [],
                    "kritik_kalem_var": False,
                }
            fd = faz_data[k.faz]
            fd["min_baslangic_hafta"] = min(fd["min_baslangic_hafta"], actual_start_hafta)
            fd["max_bitis_hafta"] = max(fd["max_bitis_hafta"], bitis_hafta_orta)
            fd["max_bitis_hafta_max"] = max(fd["max_bitis_hafta_max"], bitis_hafta_max)
            fd["kalem_sayisi"] += 1
            fd["kalemler"].append(k.isim)
            if is_kritik:
                fd["kritik_kalem_var"] = True

    # ── Toplam süreler ──
    sonuc.toplam_sure_hafta_min = max_bitis_min
    sonuc.toplam_sure_hafta_max = max_bitis_max
    sonuc.toplam_sure_ay = max_bitis_orta / 4.33
    sonuc.toplam_sure_ay_min = max_bitis_min / 4.33
    sonuc.toplam_sure_ay_max = max_bitis_max / 4.33

    sonuc.tahmini_bitis = (baslangic_tarihi + timedelta(weeks=max_bitis_orta)).strftime("%d.%m.%Y")
    sonuc.bitis_tarihi_min = (baslangic_tarihi + timedelta(weeks=max_bitis_min)).strftime("%d.%m.%Y")
    sonuc.bitis_tarihi_max = (baslangic_tarihi + timedelta(weeks=max_bitis_max)).strftime("%d.%m.%Y")

    # ── Faz özeti ──
    for faz_isim, fd in faz_data.items():
        faz_baslangic = baslangic_tarihi + timedelta(weeks=fd["min_baslangic_hafta"])
        faz_bitis = baslangic_tarihi + timedelta(weeks=fd["max_bitis_hafta"])
        faz_sure = fd["max_bitis_hafta"] - fd["min_baslangic_hafta"]

        sonuc.faz_ozeti[faz_isim] = {
            "baslangic_hafta": fd["min_baslangic_hafta"],
            "bitis_hafta": fd["max_bitis_hafta"],
            "sure_hafta": faz_sure,
            "sure_ay": round(faz_sure / 4.33, 1),
            "baslangic_tarih": faz_baslangic.strftime("%d.%m.%Y"),
            "bitis_tarih": faz_bitis.strftime("%d.%m.%Y"),
            "kalem_sayisi": fd["kalem_sayisi"],
            "kalemler": fd["kalemler"],
            "kritik_kalem_var": fd["kritik_kalem_var"],
        }

    return sonuc


def create_gantt_chart(sonuc: TimelineSonucu) -> go.Figure:
    """Plotly Gantt chart oluşturur."""
    if not sonuc.is_kalemleri:
        fig = go.Figure()
        fig.add_annotation(text="Veri yok", showarrow=False)
        return fig

    df = []
    for item in sonuc.is_kalemleri:
        df.append({
            "Task": item["isim"],
            "Start": item["baslangic"],
            "Finish": item["bitis"],
            "Resource": "Kritik Yol" if item["kritik_yol"] else "Normal",
        })

    colors = {"Kritik Yol": "#E53935", "Normal": "#1E88E5"}

    sure_min = math.ceil(sonuc.toplam_sure_ay_min) if sonuc.toplam_sure_ay_min else int(sonuc.toplam_sure_ay)
    sure_max = math.ceil(sonuc.toplam_sure_ay_max) if sonuc.toplam_sure_ay_max else int(sonuc.toplam_sure_ay)

    title_text = (
        f"İnşaat Takvimi — Tahmini {sure_min}–{sure_max} Ay"
        f" | Kritik Yol: {sonuc.kritik_yol_suresi} hafta"
    )

    fig = ff.create_gantt(
        df,
        colors=colors,
        index_col="Resource",
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title=title_text,
    )

    fig.update_layout(
        height=max(500, len(sonuc.is_kalemleri) * 28),
        xaxis_title="Tarih",
        font=dict(size=10),
        margin=dict(l=250),
    )

    return fig
