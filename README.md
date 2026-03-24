# 🏗️ İmar Uyumlu Kat Planı Üretici

Türkiye'ye özgü, parsel ölçülerinden başlayarak imar parametreleri ile uyumlu kat planları üreten, mali fizibilite ve deprem risk analizi yapan, enerji performans tahmini sunan kapsamlı bir Streamlit platformu.

## 🚀 Kurulum

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📋 Fazlar

| Faz | Açıklama | Durum |
|-----|----------|-------|
| FAZ 1 | Parsel Girişi + İmar + Hesaplama + Daire Bölümleme | ✅ |
| FAZ 2 | Veri Seti Kuralları (80K+ plan istatistikleri) | ✅ |
| FAZ 3 | Dual AI Plan Üretim Motoru (Claude + Grok) | ✅ |
| FAZ 4 | İteratif İyileştirme + Mobilya Yerleştirme | ✅ |
| FAZ 5 | 3D Görselleştirme (Plotly 3D) | ✅ |
| FAZ 6 | Harita/Güneş Analizi + Fotogerçekçi Render | ✅ |
| FAZ 7 | Mali Analiz + Deprem + Enerji + Gantt + Belgeler | ✅ |

## 🏛️ Mimari

```
app.py                  → Ana Streamlit uygulaması (25 sayfa)
core/                   → Parsel, imar hesaplama, daire bölümleme, plan üretimi
config/                 → Yapı yönetmeliği kuralları, oda varsayılanları
ai/                     → Dual AI motoru (Claude + Grok)
dataset/                → 80K+ plan istatistiksel kuralları
analysis/               → Deprem, enerji, güneş, maliyet, fizibilite
drawing/                → SVG/matplotlib/DXF plan çizimi
visualization_3d/       → Plotly 3D bina modeli
map/                    → Folium harita, güneş analizi
legal/                  → Kat irtifakı, ruhsat belgeleri
export/                 → PDF/SVG/DXF/PNG dışa aktarma
database/               → SQLAlchemy + SQLite
utils/                  → Geometri, validasyon, sabitler
```

## 📐 Özellikler

- **Parsel Geometrisi:** Dikdörtgen, dörtgen, beşgen, altıgen, düzensiz parsel desteği
- **İmar Hesaplama:** TAKS/KAKS, çekme mesafeleri, ortak alan düşümü
- **Daire Bölümleme:** 1+1 → 5+1 şablonları, düzenlenebilir oda tablosu
- **Kat Planı Üretimi:** Dual AI (Claude + Grok) ile 4 alternatif + puanlama
- **3D Görselleştirme:** Plotly ile interaktif bina modeli
- **Mali Fizibilite:** Maliyet/gelir/kâr hesabı + duyarlılık analizi
- **Deprem Risk:** AFAD verileri + TBDY 2018 parametreleri
- **Enerji Performansı:** A-G sınıfı tahmini
- **İnşaat Süresi:** Gantt chart ile proje takvimi
- **Belge Hazırlama:** Kat irtifakı, ruhsat paketi taslakları

## 🇹🇷 Türk Yapı Yönetmeliği

Platform, Planlı Alanlar İmar Yönetmeliği kurallarını otomatik kontrol eder:
- Minimum oda alanları
- Merdiven, koridor, kapı ölçüleri
- Asansör zorunluluğu
- Islak hacim kuralları
- Yangın güvenliği

---

*Otonom Reklam Ajansı tarafından geliştirilmektedir.*
