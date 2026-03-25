# İmar Uyumlu Kat Planı Üretici

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/Lisans-MIT-green)

Türkiye'ye özgü, parsel ölçülerinden başlayarak imar parametreleri ile uyumlu kat planları üreten kapsamlı bir Streamlit platformu. Dual AI motoru (Claude + Grok), mali fizibilite, deprem risk analizi, enerji performans tahmini ve yasal belge hazırlama işlevlerini tek çatı altında sunar.

---

## Özellikler

| FAZ | Açıklama | Durum |
|-----|----------|-------|
| FAZ 1 | Parsel Girişi + İmar Hesaplama + Daire Bölümleme | Tamamlandı |
| FAZ 2 | Veri Seti Kuralları (80.000+ plan istatistikleri) | Tamamlandı |
| FAZ 3 | Dual AI Plan Üretim Motoru (Claude + Grok) | Tamamlandı |
| FAZ 4 | İteratif İyileştirme + Mobilya Yerleştirme | Tamamlandı |
| FAZ 5 | 3D Görselleştirme (Plotly 3D) | Tamamlandı |
| FAZ 6 | Harita/Güneş Analizi + Fotogerçekçi Render | Tamamlandı |
| FAZ 7 | Mali Analiz + Deprem + Enerji + Gantt + Belgeler | Tamamlandı |

**Öne çıkan özellikler:**

- **Parsel Geometrisi:** Dikdörtgen, dörtgen, beşgen, altıgen ve düzensiz parsel desteği
- **İmar Hesaplama:** TAKS/KAKS, çekme mesafeleri, emsal harici alan düşümü (Planlı Alanlar İmar Yönetmeliği)
- **Daire Bölümleme:** 1+1 — 5+1 şablonları, düzenlenebilir oda tablosu
- **Kat Planı Üretimi:** Dual AI (Claude + Grok) ile 4 alternatif plan + otomatik puanlama
- **3D Görselleştirme:** Plotly ile interaktif bina modeli
- **Mali Fizibilite:** Maliyet / gelir / kâr hesabı ve duyarlılık analizi
- **Deprem Risk Analizi:** AFAD verileri + TBDY 2018 parametreleri
- **Enerji Performansı:** A–G sınıfı tahmini
- **İnşaat Takvimi:** Gantt chart ile proje zaman çizelgesi
- **Yasal Belgeler:** Kat irtifakı ve ruhsat paketi taslakları

---

## Ekran Görüntüleri

> Ekran görüntüleri yakında eklenecektir.

---

## Hızlı Başlangıç (Kurulum)

```bash
git clone https://github.com/Ahmet571-es/imar-plan-uretici.git
cd imar-plan-uretici
pip install -r requirements.txt
streamlit run app.py
```

Uygulama varsayılan olarak `http://localhost:8501` adresinde açılır.

**Gereksinimler:**
- Python 3.11+
- AI özellikleri için `ANTHROPIC_API_KEY` ve `OPENAI_API_KEY` ortam değişkenleri

---

## Proje Yapısı

```
imar-plan-uretici/
├── app.py                     # Ana Streamlit uygulaması (25 sayfa)
├── requirements.txt
├── pyproject.toml             # Pytest + Ruff yapılandırması
├── core/                      # Parsel, imar hesaplama, daire bölümleme, plan üretimi
│   ├── parcel.py
│   ├── zoning.py
│   ├── apartment_divider.py
│   ├── floor_plan_generator.py
│   ├── furniture_placer.py
│   └── plan_scorer.py
├── config/                    # Yapı yönetmeliği kuralları, oda ve maliyet varsayılanları
├── ai/                        # Dual AI motoru (Claude + Grok), konsensüs, çapraz inceleme
├── agents/                    # Otonom ajan sistemi (orkestratör, optimizasyon ajanları)
├── dataset/                   # 80.000+ plan istatistiksel kuralları
├── analysis/                  # Deprem, enerji, güneş, maliyet, fizibilite, gelir
├── drawing/                   # SVG / Matplotlib / DXF plan çizimi
├── visualization_3d/          # Plotly 3D bina modeli
├── map/                       # Folium harita, güneş analizi
├── legal/                     # Kat irtifakı, ruhsat belgeleri
├── export/                    # PDF / SVG / DXF / PNG dışa aktarma
├── database/                  # SQLAlchemy + SQLite
├── pages/                     # Streamlit çok sayfalı yapı modülleri
├── utils/                     # Geometri yardımcıları, validasyon, sabitler
└── tests/                     # 111 pytest testi
```

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Arayüz | Streamlit 1.30+ |
| AI | Anthropic Claude, OpenAI (Grok) |
| Geometri | Shapely 2.0 |
| Veri / Tablo | NumPy, Pandas |
| Grafik / Çizim | Matplotlib, Plotly, svgwrite |
| Harita | Folium, streamlit-folium, pyproj |
| CAD Çıktısı | ezdxf |
| PDF | ReportLab |
| Veritabanı | SQLAlchemy + SQLite |
| Test | pytest |
| Linting | Ruff |

---

## Testleri Çalıştırma

```bash
# Tüm testleri çalıştır
pytest

# Ayrıntılı çıktı ile
pytest -v

# Belirli bir test dosyası
pytest tests/test_imar_hesaplama.py -v

# Belirli bir test sınıfı
pytest tests/test_finansal.py::TestMaliyetHesaplama -v
```

Proje genelinde **111 test** bulunmaktadır. Test yapılandırması `pyproject.toml` dosyasında yer almaktadır.

---

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

## Katkıda Bulunma

Katkılarınız memnuniyetle karşılanır. Lütfen şu adımları izleyin:

1. Projeyi fork edin
2. Özellik dalı oluşturun: `git checkout -b ozellik/yeni-ozellik`
3. Değişikliklerinizi commit edin: `git commit -m 'Yeni özellik eklendi'`
4. Dalı push edin: `git push origin ozellik/yeni-ozellik`
5. Pull Request açın

Kod stili için `ruff` linter kullanılmaktadır (`pyproject.toml` yapılandırmasına göre, satır uzunluğu 120, Python 3.11 hedefi).
