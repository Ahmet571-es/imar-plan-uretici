"""
İnşaat Süresi Tahmini — Gantt chart ile proje takvimi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import plotly.figure_factory as ff
import plotly.graph_objects as go


@dataclass
class IsKalemi:
    """Bir iş kalemi."""
    isim: str
    sure_hafta_min: int
    sure_hafta_max: int
    baslangic_offset_hafta: int = 0  # Projenin başlangıcından itibaren
    paralel_grup: str = ""           # Paralel çalışabilecek iş grubu
    kritik_yol: bool = False


# ── İş kalemleri şablonu (konut bina) ──
def get_is_kalemleri(kat_sayisi: int = 4, bodrum_var: bool = False) -> list[IsKalemi]:
    """Kat sayısına göre iş kalemlerini oluşturur."""
    kaba_per_kat = 2.5  # hafta/kat
    kaba_sure = int(kat_sayisi * kaba_per_kat)

    kalemler = [
        IsKalemi("Hafriyat & Temel", 3, 4, 0, "temel", True),
    ]

    offset = 4
    if bodrum_var:
        kalemler.append(IsKalemi("Bodrum Kat", 3, 4, offset, "temel", True))
        offset += 4

    kalemler.extend([
        IsKalemi(f"Kaba İnşaat ({kat_sayisi} kat)", kaba_sure, kaba_sure + 4, offset, "kaba", True),
        IsKalemi("Çatı", 2, 3, offset + kaba_sure, "kaba", True),
        IsKalemi("Dış Cephe & Mantolama", 4, 6, offset + kaba_sure - 4, "dis_cephe", False),
        IsKalemi("Tesisat (Elektrik/Su)", 4, 6, offset + int(kaba_sure * 0.4), "tesisat", False),
        IsKalemi("Sıva & Boya", 4, 6, offset + kaba_sure + 2, "ince", True),
        IsKalemi("Döşeme & Kaplama", 3, 4, offset + kaba_sure + 8, "ince", True),
        IsKalemi("Mutfak & Banyo", 3, 4, offset + kaba_sure + 10, "ince", False),
        IsKalemi("Kapı & Pencere Montajı", 2, 3, offset + kaba_sure + 6, "montaj", False),
        IsKalemi("Asansör Montajı", 3, 4, offset + kaba_sure + 4, "montaj", False),
        IsKalemi("Çevre Düzeni", 2, 3, offset + kaba_sure + 12, "cevre", False),
        IsKalemi("Temizlik & Kontrol", 1, 2, offset + kaba_sure + 14, "final", True),
        IsKalemi("İskan Başvurusu", 2, 4, offset + kaba_sure + 16, "final", True),
    ])

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

    max_bitis = 0
    for k in kalemler:
        orta_sure = (k.sure_hafta_min + k.sure_hafta_max) // 2
        bitis = k.baslangic_offset_hafta + orta_sure
        max_bitis = max(max_bitis, bitis)

        baslangic = baslangic_tarihi + timedelta(weeks=k.baslangic_offset_hafta)
        bitis_tarih = baslangic + timedelta(weeks=orta_sure)

        sonuc.is_kalemleri.append({
            "isim": k.isim,
            "sure_hafta": orta_sure,
            "baslangic": baslangic.strftime("%Y-%m-%d"),
            "bitis": bitis_tarih.strftime("%Y-%m-%d"),
            "kritik_yol": k.kritik_yol,
        })

    sonuc.toplam_sure_hafta_min = max_bitis - 4
    sonuc.toplam_sure_hafta_max = max_bitis + 4
    sonuc.toplam_sure_ay = max_bitis / 4.33
    sonuc.tahmini_bitis = (baslangic_tarihi + timedelta(weeks=max_bitis)).strftime("%d.%m.%Y")

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

    fig = ff.create_gantt(
        df,
        colors=colors,
        index_col="Resource",
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title=f"İnşaat Takvimi — Tahmini {sonuc.toplam_sure_ay:.0f} Ay",
    )

    fig.update_layout(
        height=500,
        xaxis_title="Tarih",
        font=dict(size=10),
        margin=dict(l=200),
    )

    return fig
