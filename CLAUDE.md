# CLAUDE.md — Proje Rehberi

Bu dosya, Claude Code'un (ve geliştiricilerin) proje hakkında hızlıca bilgi edinmesi için hazırlanmıştır.

---

## Proje Özeti

**İmar Uyumlu Kat Planı Üretici** — Türkiye'ye özgü parsel ölçüleri ve imar parametrelerinden başlayarak kat planları üreten kapsamlı bir Streamlit platformudur. Dual AI motoru (Claude + Grok), mali fizibilite, deprem risk analizi, enerji performans tahmini ve yasal belge hazırlama işlevlerini tek çatı altında sunar.

---

## Sürüm Durumu

| Bilgi | Değer |
|-------|-------|
| Güncel sürüm | **v1.2.0** |
| Python | 3.11+ |
| Test sayısı | **111 test** (5 dosya) |
| Toplam Python dosyası | **76 dosya** |
| Toplam satır sayısı | **~15 065 satır** |

---

## Komutlar

```bash
# Uygulamayı çalıştır
streamlit run app.py

# Tüm testleri çalıştır
pytest

# Ayrıntılı test çıktısı
pytest -v

# Belirli test dosyası
pytest tests/test_imar_hesaplama.py -v

# Belirli test sınıfı
pytest tests/test_finansal.py::TestMaliyetHesaplama -v

# Linting
ruff check .
ruff check . --fix
```

**Gerekli Ortam Değişkenleri:**

```bash
ANTHROPIC_API_KEY=sk-ant-...   # Claude AI
OPENAI_API_KEY=sk-...          # Grok (OpenAI uyumlu endpoint)
```

---

## Mimari

### Ana Dosya

| Dosya | Satır | Açıklama |
|-------|-------|----------|
| `app.py` | 1 339 | Ana Streamlit uygulaması (25 sayfa) |

### Modüller

| Modül | Dosyalar | Açıklama |
|-------|----------|----------|
| `core/` | 7 dosya | Parsel, imar hesaplama, daire bölümleme, plan üretimi, puanlama |
| `config/` | 4 dosya | Yapı yönetmeliği kuralları, oda ve maliyet varsayılanları, mobilya kütüphanesi |
| `ai/` | 6 dosya | Dual AI motoru (Claude + Grok), konsensüs, çapraz inceleme, render üretici |
| `agents/` | 8 dosya | Otonom ajan sistemi — orkestratör, optimizasyon ajanları |
| `dataset/` | 2 dosya | 80 000+ plan istatistiksel kuralları ve kural çıkarma motoru |
| `analysis/` | 8 dosya | Deprem, enerji, güneş, maliyet, fizibilite, gelir, takvim, parsel karşılaştırma |
| `drawing/` | 1 dosya | Matplotlib plan çizici |
| `visualization_3d/` | 1 dosya | Plotly 3D bina modeli |
| `map/` | 1 dosya | Folium harita + konum seçici |
| `legal/` | 2 dosya | Kat irtifakı ve ruhsat belgeleri taslakları |
| `export/` | 3 dosya | PDF / SVG / DXF dışa aktarma ve fizibilite raporu |
| `database/` | 1 dosya | SQLAlchemy + SQLite proje veritabanı |
| `pages/` | 3 dosya | Streamlit sayfa mantığı (tasarım, analiz, diğer) |
| `utils/` | 5 dosya | Geometri yardımcıları, doğrulama, sabitler, navigasyon, güvenli import |
| `tests/` | 6 dosya | 111 pytest testi + ortak fixture'lar |

---

## Önemli Dosyalar

### `core/zoning.py` (332 satır)

- **`ImarParametreleri`** — imar verilerini tutan dataclass (kat adedi, nizam, TAKS, KAKS, bahçe mesafeleri, bina yüksekliği limiti, sığınak flag)
- **`EmsalHariciAlanlar`** — emsal harici alan hesabı sonuç dataclass
- **`HesaplamaSonucu`** — tam hesaplama çıktısı (inşaat alanı, kat adedi, uyarılar)
- **`hesapla(parsel_polygon, imar)`** — ana hesaplama fonksiyonu

### `core/floor_plan_generator.py` (1 120 satır)

- **`RoomSlot`** — oda yerleşim slotu dataclass
- **`generate_professional_plan()`** — profesyonel kat planı üretici (ana giriş noktası)
- **`generate_multiple_plans()`** — birden fazla alternatif plan üretir
- **`generate_dual_apartment_plan()`** — çift daireli kat planı

### `core/plan_scorer.py` (278 satır)

- **`PlanRoom`** — plan odası dataclass (oda tipi, koordinatlar, pencere/kapı listesi)
- **`FloorPlan`** — tam kat planı dataclass
- **`ScoreBreakdown`** — puanlama detayları dataclass
- **`score_plan()`** — kat planını 0–100 arasında puanlar

### `core/parcel.py` (216 satır)

- **`Parsel`** — parsel dataclass (il, ilçe, ada, parsel no, koordinatlar, alan, şekil tipi)

### `core/apartment_divider.py` (216 satır)

- **`Oda`**, **`Daire`**, **`KatPlani`**, **`BinaProgrami`** — hiyerarşik veri modeli
- **`varsayilan_daireler_olustur()`** — 1+1–5+1 şablon daire listesi üretir

### `core/tkgm_api.py` (324 satır)

- **`TKGMParselSonuc`** — TKGM sorgulama sonuç dataclass
- **`parsel_sorgula()`** — TKGM CBS ve WFS API entegrasyonu
- **`test_tkgm_connection()`** — bağlantı testi

### `utils/constants.py` (101 satır)

Tüm sabitler tek dosyada toplanmıştır:

| Grup | Örnek Sabitler |
|------|---------------|
| Duvar kalınlıkları | `DIS_DUVAR_KALINLIK`, `IC_TASIYICI_DUVAR_KALINLIK`, `IC_BOLME_DUVAR_KALINLIK`, `MANTOLAMA_KALINLIK` |
| Kat yükseklikleri | `KAT_YUKSEKLIGI`, `IC_YUKSEKLIK`, `ISLAK_HACIM_IC_YUKSEKLIK`, `DOSEME_KALINLIK` |
| Kapı boyutları | `BINA_GIRIS_KAPI_GENISLIK`, `DAIRE_GIRIS_KAPI_GENISLIK`, `IC_KAPI_GENISLIK`, `KAPI_YUKSEKLIK` |
| Pencere boyutları | `PENCERE_ALT_SEVIYE`, `PENCERE_YUKSEKLIK`, `PENCERE_MIN_KOSEDEN_MESAFE` |
| Merdiven ölçüleri | `MERDIVEN_KOLU_GENISLIK`, `MERDIVEN_BASAMAK_YUKSEKLIK`, `MERDIVEN_EVI_ALAN` |
| Asansör ölçüleri | `ASANSOR_KABIN_MIN_EN`, `ASANSOR_KABIN_MIN_BOY`, `ASANSOR_KUYU_ALAN`, `ASANSOR_ZORUNLU_KAT` |
| Koridor ölçüleri | `BINA_GIRIS_KORIDOR_MIN`, `DAIRE_IC_KORIDOR_MIN`, `KORIDOR_IDEAL_GENISLIK` |
| Ortak alan tahminleri | `GIRIS_HOLU_ALAN`, `SIGINAK_ORAN`, `TEKNIK_HACIM_ALAN`, `OTOPARK_ALAN_ARAC_BASI` |
| Emsal harici alanlar | `EMSAL_HARICI_MERDIVEN`, `EMSAL_HARICI_ASANSOR`, `EMSAL_HARICI_GIRIS_HOLU`, `EMSAL_HARICI_SIGINAK_ORAN`, `EMSAL_HARICI_TEKNIK_HACIM`, `EMSAL_HARICI_OTOPARK_ARAC` |
| İmar varsayılanları | `VARSAYILAN_TAKS`, `VARSAYILAN_KAKS`, `VARSAYILAN_KAT_ADEDI`, `VARSAYILAN_ON_BAHCE`, `VARSAYILAN_YAN_BAHCE`, `VARSAYILAN_ARKA_BAHCE` |
| İnşaat nizamları | `INSAAT_NIZAMLARI` (A/B/BL) |
| Daire tipleri | `DAIRE_TIPLERI` (1+1–5+1) |
| Balkon | `BALKON_KORKULUK_YUKSEKLIK`, `BALKON_MIN_DERINLIK` |
| Yangın güvenliği | `KACIS_KAPI_MIN_GENISLIK`, `MAX_YUKSEKLIK_DIS_MERDIVEN` |
| Hava bacası / ışıklık | `HAVA_BACASI_MIN_EN`, `HAVA_BACASI_MIN_BOY`, `ISIKLIK_MAX_HACIM` |
| Çizim sabitleri | `CIZIM_DIS_DUVAR_PX`, `CIZIM_IC_TASIYICI_PX`, `CIZIM_IC_BOLME_PX`, `CIZIM_OLCEK` |

### `ai/dual_ai_engine.py` (179 satır)

- **`PlanAlternatif`**, **`DualAIResult`** — AI çıktı dataclass'ları
- **`generate_dual_ai_plans()`** — Claude ve Grok planlarını birleştirir, konsensüs uygular

### `agents/base_agent.py`

- **`BaseAgent`** — tüm ajanların miras aldığı soyut temel sınıf
- **`AgentMessage`**, **`AgentRun`** — SQLAlchemy ORM modelleri (ajan mesajları ve çalıştırma geçmişi)

### `analysis/earthquake_risk.py`

- **`DepremAnalizi`** — deprem risk analizi sonuç dataclass (AFAD + TBDY 2018)
- **`KolonGrid`** — kolon ızgarası dataclass
- **`deprem_risk_analizi()`** — ana analiz fonksiyonu
- **`test_afad_api()`** — AFAD API bağlantı testi

### `utils/safe_import.py`

- **`safe_import()`** — opsiyonel bağımlılıkları hata vermeden yükler
- **`is_available()`** — modülün kurulu olup olmadığını kontrol eder
- **`require_or_warn()`** — eksik bağımlılık için Streamlit uyarısı gösterir

---

## Test Altyapısı

Yapılandırma `pyproject.toml` içindedir:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
filterwarnings = ["ignore::DeprecationWarning", "ignore::UserWarning"]
```

### Test Dosyaları

| Dosya | Test Sayısı | Kapsam |
|-------|-------------|--------|
| `tests/conftest.py` | — | Ortak fixture'lar (parsel geometrileri, imar parametreleri) |
| `tests/test_imar_hesaplama.py` | 30 | İmar ve parsel hesaplama |
| `tests/test_floor_plan.py` | 30 | Kat planı üretimi ve puanlama |
| `tests/test_finansal.py` | 19 | Maliyet, gelir ve fizibilite |
| `tests/test_konum.py` | 18 | Harita, güneş ve konum analizi |
| `tests/test_agents.py` | 14 | Ajan sistemi |
| **Toplam** | **111** | |

### Ortak Fixture'lar (`conftest.py`)

- `dikdortgen_parsel_22x28` — 616 m² standart parsel
- `dikdortgen_parsel_10x15` — 150 m² küçük parsel
- `kucuk_parsel_5x10` — 50 m² çok küçük parsel
- `buyuk_parsel_100x100` — 10 000 m² büyük parsel
- `cokgen_parsel_5_kenar` — 5 kenarlı düzensiz parsel
- `varsayilan_imar` — Ayrık nizam, 4 kat, TAKS 0.35, KAKS 1.40
- `bitisik_nizam_imar` — Bitişik nizam, 5 kat
- `imar_3_kat` — Asansör zorunlu olmayan 3 katlı imar
- `imar_yukseklik_limitli` — Bina yüksekliği sınırlı imar
- `imar_sifir_taks_kaks` — Sınır durumu testi (TAKS/KAKS = 0)
- `imar_arka_bahce_sifir` — H/2 kuralını tetikleyen imar
- `imar_siginakli` — Sığınak gerekli imar

---

## Linting

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]
```

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Arayüz | Streamlit 1.30+ |
| AI | Anthropic Claude API, OpenAI API (Grok) |
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

## Önemli Notlar

- **Demo modu:** AI API anahtarları sağlanmadan da uygulama çalışır; bu durumda `_generate_demo_plans()` / `_generate_grok_demo()` fonksiyonları örnek planlar üretir.
- **Emsal harici alan:** Hesaplamalar Planlı Alanlar İmar Yönetmeliği'ne dayanır; merdiven evi (18 m²) ve asansör kuyusu (7 m²) her katta KAKS'tan düşülür.
- **H/2 kuralı:** `arka_bahce = 0` girildiğinde `_arka_bahce_h_yari_kurali()` devreye girer ve bina yüksekliğinin yarısı arka bahçe mesafesi olarak hesaplanır.
- **Asansör zorunluluğu:** `ASANSOR_ZORUNLU_KAT = 4` — 4 ve üzeri katlı binalarda asansör şartı kontrol edilir.
- **Rate limiting:** `ai/claude_planner.py` içinde yerleşik Claude API rate-limit koruyucusu bulunur (`_check_rate_limit()`, `_record_request()`).
- **TKGM entegrasyonu:** `core/tkgm_api.py` CBS ve WFS API uç noktalarını dener; başarısız olursa manuel koordinat girişine döner.
